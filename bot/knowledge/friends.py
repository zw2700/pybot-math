"""Friends and relationships: money between friends, a friend gone quiet, saying a plain no.

The replies give the actual sentence to say, because that is the part people are stuck on.
Birthdays and making friends are in bot/knowledge/family.py; a message to cancel dinner is
bot/knowledge/wording.py's, so neither is repeated here.
"""
import re

from ..compose.repair import owns_the_deed
from .dishes import KEEP_QUALITY_WORDS
from .lookup import entry
from .wording import TALKING_IS_NOT_A_CHAT


_COOKING_FOR_THEM = re.compile(
    r"\b(?:cook|cooks|cooking|cooked|make|makes|making|made|bake|baking|roast|roasting|"
    r"hosting|prepare|preparing)\b[^.?!]{0,30}\b(?:for|to)\b", re.IGNORECASE)


def _not_cooking_for_them(understood):
    """False when the line is about cooking for the people it names, not meeting them."""
    if not isinstance(understood, dict):
        return True
    said = str(understood.get("clean") or understood.get("text") or "")
    return not _COOKING_FOR_THEM.search(said)

ANSWERS = ("friends-and-relationships",)
# "something nice for my girlfriend on friday" names a person and a gesture, and no mood. It was
# getting the cheer-up script - "send one message today saying you have been thinking of them" -
# because the gift-shaped phrase "something nice for" was enough on its own once the person was
# named. That phrase asks for a treat, and only reads as comfort when the line also says the person
# is low: "something nice for my friend who is sad" keeps the script, while the plain gesture is
# left to the rows about presents and cooking for someone.
_GESTURE = re.compile(
    r"\b(?:something|somethin|anything|a thing|things|a present|a gift)\b"
    r"[^.?!]{0,20}\b(?:nice|good|kind|special|lovely)\b"
    r"|\bnice (?:little )?thing to do for\b"
    r"|\bdo something nice for\b", re.IGNORECASE)
_LOW_MOOD = re.compile(
    r"\b(?:sad|sadness|down|low|upset|unhappy|miserable|struggl\w*|rough time|hard time|"
    r"bad time|going through|cry|cries|crying|cried|bad news|not themselves?|not himself|"
    r"not herself|in a rut|stressed|grie\w*|bereave\w*|lonely|loneliness|depress\w*|"
    r"anxious|worried|hurt|cheer\w*|comfort\w*|console\w*|feel better|"
    r"having a hard)\b", re.IGNORECASE)


def _not_a_plain_gesture(understood):
    """False when the line asks for a treat for someone and says nothing about how they are."""
    if not isinstance(understood, dict):
        return True
    said = str(understood.get("clean") or understood.get("text") or "")
    if not _GESTURE.search(said):
        return True
    return bool(_LOW_MOOD.search(said))



# "how do i stop feeling sick", "how do i stop feeling dizzy" and "how do i stop feeling tired all
# the time" all reached hard-conversation: the row keys "how i feel", the matcher reads "feeling"
# as that, and "how" is in its second group, so a question about a body got the card about saying a
# hard thing to someone. A hard conversation is about a person or about the talk itself, so the
# row now asks the line to name one of those before it answers. "how do i talk about my feelings"
# names the talk and still reaches it.
_THE_PERSON = (
    "my husband", "my wife", "my partner", "my boyfriend", "my girlfriend", "my fiance",
    "my friend", "my best friend", "my mate", "my mum", "my mom", "my mother",
    "my dad", "my father", "my parents", "my sister", "my brother", "my son", "my daughter",
    "my child", "my teenager", "my flatmate", "my housemate", "my roommate", "my landlord",
    "my boss", "my manager", "my colleague", "my coworker", "my team", "my neighbour",
    "my neighbor", "my mother in law", "my mother-in-law", "my in laws", "my ex", "my family",
    "a friend", "a colleague", "a coworker", "a flatmate", "a neighbour", "a family member",
    "someone at work", "with her", "with him", "with them", "to her", "to him", "to them",
    "tell her", "tell him", "tell them", "ask her", "ask him", "ask them")
# the talk itself, when no person is named: "how do i talk about my feelings" is this row's line
# even though it names nobody.
_THE_TALK = (
    "conversation", "bring it up", "bring something up", "bring this up", "have it out",
    "open up", "my feelings", "about my feelings", "how i feel", "how i really feel",
    "confront", "confronting", "confrontation", "the subject", "broach", "hard talk")


def _names_a_person_and_is_not_a_deed(understood):
    """`_names_a_person_or_the_talk`, and not a line where the hurt is the speaker's own to mend.

    "i hurt my husbands feelings" names a person and the talk, so this row was reached - but the
    script it gives is for raising a complaint of their own, and the answer they need is what to do
    about the hurt (bot/compose/repair.py).
    """
    return _names_a_person_or_the_talk(understood) and not owns_the_deed(understood)


def _names_a_person_or_the_talk(understood):
    """A hard conversation is about someone, or about the talk; a body is neither."""
    words = " ".join(str(word).lower() for word in understood.get("words") or ())
    whole = " %s " % " ".join(words.split())
    return any(part in whole for part in _THE_PERSON + _THE_TALK)


# "How do I help them" is one question whatever the second half is: a friend crying, a mate
# having a hard time, a partner who is stressed. Those lines hedged on main - they carry no
# "cheer up", no "comfort" and no "what do i say", which are the words the cheer-up row is keyed
# on - so they reached nothing at all. The help being asked for is the cheer-up advice, which is
# what the entry below carries; the help shape is its own row because the person and the trouble
# are the whole question rather than a word in it.
# The third part is in `ask`, not in the key: a person and "how do i help" are two parts of three,
# which is a match, and that read "how do i help my son with his reading" and "how do i help my
# wife with the housework" as a friend in trouble. The trouble is stated in the line or the row
# stands down.
HELPING_ASK = ("how do i help", "how can i help", "how do i best help", "how can i best help",
               "how do i support", "how can i support", "how best to support",
               "what do i do", "what should i do", "what can i do", "what could i do",
               "how do i start helping",
               "help them through", "help him through", "help her through",
               "help them cope", "help him cope", "help her cope")
HELPING_PERSON = ("friend", "friends", "mate", "mates", "best friend", "best mate", "bestie",
                  "partner", "husband", "wife", "boyfriend", "girlfriend", "fiance", "fiancee",
                  "mum", "mother", "mam", "dad", "father", "parent", "parents", "sister",
                  "brother", "son", "daughter", "child", "someone", "somebody", "person",
                  "colleague", "coworker", "neighbour", "neighbor", "them", "him", "her")
HELPING_TROUBLE = ("sad", "sadness", "down", "upset", "unhappy", "miserable", "struggling",
                   "rough time", "hard time", "bad time", "going through", "crying", "cried",
                   "cries", "tears", "bad news", "having a hard", "not themselves", "in a rut",
                   "stressed", "devastated", "hurting", "in bits", "broken",
                   "shut down", "shutting down", "grieving", "lost their", "lost his",
                   "lost her", "whose", "died", "death", "ill", "unwell", "in hospital")

# "how do you say goodbye in irish" is the phrasebook's line, and the exit card reads the same two
# words. A line that puts the saying in a language is asking for the words, not for a script.
_SAID_IN_A_LANGUAGE = re.compile(
    r"\bin (?:welsh|cymraeg|irish|gaeilge|scots|gaelic|french|spanish|espanol|portuguese|italian|"
    r"german|deutsch|dutch|polish|russian|greek|turkish|arabic|hebrew|hindi|urdu|bengali|punjabi|"
    r"japanese|chinese|mandarin|cantonese|korean|thai|vietnamese|swedish|norwegian|danish|"
    r"finnish|icelandic|latin)\b"
    r"|\b(?:translate|translation|pronounce)\b")


def said_in_a_language(understood):
    """True when the line asks for the words in another language, which is study.py's question."""
    text = (understood.get("clean") or understood.get("text") or "").lower()
    return bool(_SAID_IN_A_LANGUAGE.search(text))


ENTRIES = [
    # --- what a behaviour means, and what to say to it ----------------------------
    # "what does it mean when someone is passive aggressive" was a shrug: the answer is what the
    # behaviour is and the one sentence that names it without a fight.
    entry("passive-aggressive-backhanded", (("passive aggressive", "passive-aggressive", "passive agressive",
                                  "passive agression", "passive aggression", "being passive"),
                                 ("mean", "means", "meaning", "what does", "what is", "why",
                                  "someone", "friend", "mum", "mother", "sister", "brother",
                                  "colleague", "boss", "partner", "husband", "wife",
                                  "coworker", "deal with", "handle", "respond", "reply")),
          "Passive aggression is anger shown by what a person does not say: a flat 'fine', a sigh, "
          "a joke with an edge, being left out of the group chat, help that quietly stops. Treat it "
          "as anger that hasn't found words and name the behaviour once, plainly: 'You seemed "
          "annoyed when I said that - did it land badly?' Ask about the thing, not the tone, and "
          "don't answer it in kind; matching the silence is what turns a week into a year."),
    # "why is my friend being off with me" landed on the gift-budget row, which shares the word
    # friend. Being off with you is its own question, so it gets its own row.
    entry("off-with-me", (("friend", "friends", "mate", "bestie", "sister", "brother",
                           "colleague", "mum", "mother", "dad", "father", "they", "he", "she",
                           "someone", "somebody", "husband", "wife", "partner", "boyfriend",
                           "girlfriend",
                           # "my mrs is in a mood with me" is the same line said the way people
                           # say it at home, and none of the household words were in here
                           "mrs", "missus", "oh", "hubby", "other half", "the wife",
                           "the husband", "fella", "lad", "bloke"),
                          # "off with" alone is the order of a trip ("off with my husband and
                          # our two kids"), not a person who is off with the speaker: the person
                          # has to be the one who is off, so only the phrase with "me" in it.
                          ("off with me", "being off", "short with me", "snappy",
                           "cold with me", "distant with me", "weird with me", "off hand",
                           "offhand", "gone cold", "gone quiet with me", "annoyed", "upset",
                           "angry", "cross with me", "miffed", "pissed off", "not talking to me",
                           "ignoring me",
                           # "my partner is mad at me" and "my partner is furious with me" were
                           # "Noted: your partner is mad at you" - the shape this row exists for,
                           # reached on a word the row did not hold. The phrases carry "at me" or
                           # "with me" on purpose: "my husband is in a mood" and "my girlfriend
                           # is livid" are somebody's mood about something unknown, and this card
                           # only fits a mood that is *with the person asking*.
                           "mad at me", "mad with me", "furious with me", "furious at me",
                           "livid with me", "livid at me", "a mood with me", "hump with me",
                           "got the hump with me", "not happy with me", "angry with me",
                           "angry at me", "upset with me", "upset at me", "annoyed with me",
                           "annoyed at me", "cross at me", "mardy with me", "miffed with me",
                           "mad on me")),
          "Ask once, in your own words, and make it about them rather than a list of charges: "
          "'You seem a bit off with me - have I done something?' Then leave room for the answer. If "
          "they say nothing is wrong, take it at face value and carry on as normal; most of the "
          "time it is their week and not you, and a second and third 'are you okay?' is what makes "
          "it awkward.",
          # money owed, a missed birthday or a cancelled plan is a different row's question
          avoid=("lent", "lend", "borrowed", "owes", "owe", "money", "quid", "birthday", "forgot",
                 "forgotten", "cancel", "cancelled", "canceled", "funeral", "died", "death",
                 "hospital", "cancer", "miscarriage", "pay rise", "promotion", "interview",
                 "secret santa", "gift", "present"),
          # The other direction is not this question: "my mum is upset with me" asks what to do
          # about her, and "i upset my dad what should i do" asks what to do about what they did.
          # The words are the same and the deed is the person's own, so the row stands down and
          # the composer's repair pool answers it (bot/compose/repair.py).
          guard=lambda reading: not owns_the_deed(reading)),
    entry("cant-pay-back", (("can t pay", "cant pay", "cant pay me back", "can t pay me back",
                            "pay it back", "pay back", "pay me back"),
                            ("yet", "says", "said", "won t", "afford", "next month")),
          "Take yes for an answer and put a date on it: 'No problem — when do you think you can get "
          "me some of it?' A small amount you actually receive is better than a big promise you "
          "don't. If it happens twice, say plainly that you need a plan you can rely on.", bias=1,
          # the one who owes, rather than the one who is owed, is the other direction
          avoid=("i owe", "i still owe", "owe my", "owe him", "owe her", "owe them",
                 "i cant pay", "i can t pay")),
    # A person can be named by what they do for you rather than by the relation: "i havent paid
    # the childminder" is money owed to a person as much as "i owe my mate" is, and without the
    # trade in the key the line went looking for the noun it named - the going rate for a
    # babysitter, the fault-finding card for a boiler - when what it is really about is a debt and
    # how to say it. The rule is the same one the entry already follows: the deed is paying, and
    # the second signal is a person, however the person is described.
    entry("owe-friend-money", (("i owe", "i still owe", "owe my friend", "owe my mate",
                                "owe him", "owe her", "owe them", "cant pay it back",
                                "can t pay it back", "cant pay back", "cant afford to pay",
                                "cant pay", "can t pay", "pay my friend back", "pay him back",
                                "pay her back", "pay them back",
                                "havent paid", "haven't paid", "havnt paid", "havent payed",
                                "havent payed them", "not paid", "never paid",
                                "still havent paid", "still not paid", "i still owe them",
                                "owe them for", "owe him for", "owe her for"),
                               # the person is the second signal: money owed on a card or a
                               # council tax bill is a money domain question, not this one
                               ("friend", "mate", "him", "her", "them", "back", "borrowed",
                                "lent", "tickets",
                                # a person paid for a job, by the job they do
                                "cleaner", "window cleaner", "milkman", "babysitter",
                                "baby sitter", "childminder", "child minder", "nanny",
                                "tutor", "dog walker", "dogwalker", "hairdresser", "barber",
                                "gardener", "plumber", "electrician", "builder", "painter",
                                "decorator", "carer", "sitter", "driving instructor",
                                "piano teacher", "music teacher", "swimming teacher",
                                "handyman", "odd job", "man who fixed", "woman who cleans",
                                "tradesman", "roofer", "joiner", "locksmith", "mechanic")),
          "Say it before they have to ask, and bring a number, not just an apology: 'I haven't "
          "forgotten the money I owe you. I can't do it all at once, but I can give you some of it "
          "this month and the rest by the end of next.' Then do that — a small date you keep is "
          "worth more than a big one you miss.",
          # Money owed to a person is this entry, not money.py's rent-and-bills one, which shares
          # "cant pay": "i cant pay my friend back this month what do i say" was getting the
          # StepChange answer, and tests/test_knowledge_life says which direction it should go.
          bias=1),
    # "should i forgive my brother" was "That's your call, not mine", "i cant forgive my sister"
    # was "Got it", and "is forgiving the same as forgetting" was a search hedge: the whole
    # forgiveness question had no row. What the card does is separate the three things people
    # run together - forgiving, trusting and forgetting - because that separation is the answer
    # to all of them, and then say who does it and by when.
    # One key group, because every way of asking holds the act itself: "should i forgive my
    # brother", "i cant forgive her", "is forgiving the same as forgetting", "forgive and
    # forget", "how long does it take to forgive someone". A second group of people words sent
    # the bare ones ("is it weakness to forgive", "should i forgive, he never said sorry") to
    # nothing at all, so the act alone is the key and the other worlds are fenced off below.
    entry("forgive-someone", ((
        # the act, in every form people type it
        "forgive", "forgiving", "forgiveness", "forgave", "forgiven", "forgives",
        "forgiv", "4give",
        # and the ways it comes with a question attached: with the act alone as the key,
        # "should i forgive my brother" and "is it weakness to forgive" were "That's your
        # call", because one bare word scores no more than a phrase's first word.
        "should i forgive", "should i forgiv", "can i forgive", "do i forgive",
        "could i forgive", "is it ok to forgive", "is it ok not to forgive",
        "is it wrong to forgive", "is it weakness to forgive", "weak to forgive",
        "how do i forgive", "how to forgive", "how can i forgive", "how do you forgive",
        "cant forgive", "can t forgive", "cannot forgive", "wont forgive", "won t forgive",
        "able to forgive", "not forgiving", "never forgive", "to forgive someone",
        "forgive someone", "forgiving someone", "forgive and forget",
        "forgiving and forgetting", "forgiving the same", "same as forgetting",
        "forgiving mean", "means forgiving", "forgiveness mean", "worth forgiving",
        "i forgave", "i have forgiven", "i cant forgive", "i can t forgive",
        "i wont forgive", "i won t forgive", "i need to forgive", "i want to forgive",
        "i should forgive", "i will forgive", "i never forgive",
        "have to forgive", "must i forgive", "need to forgive", "to forgive",
        "long to forgive", "take to forgive", "forgive my", "forgave my", "forgiving my",
        # forgiving is nearly always the act plus the person, so those pairs are keys too:
        # "i forgave him" and "forgiveness is hard" scored nothing with the act alone, because
        # one word on its own is worth no points at all.
        "forgive him", "forgive her", "forgive them", "forgive the", "forgive that",
        "forgave him", "forgave her", "forgave them", "forgiving him", "forgiving her",
        "forgiveness is", "is forgiveness", "forgiveness has", "forgiveness takes",
        "hard to forgive", "forgive hard", "forgiving hard", "forgive someone who",
        "forgive a person", "forgive people", "forgive the person",
    )),
          "Forgiving is not saying it was fine, and it is not trusting them again: it is "
          "deciding to stop charging them for it, so the thing stops running your week. Do it as "
          "a decision rather than waiting to feel warm about them, and say what you are dropping "
          "- 'I am not bringing this up again, and I am not pretending it did not happen.' You "
          "can forgive someone and still keep them at arm's length, and nobody is owed the words "
          "back until they have said sorry.",
          # The act in the line is the whole subject of it, so where a bare "forgive" ties with
          # a neighbour row or a fallback this is the row that should answer: the card says
          # which of forgiving, trusting and forgetting the person is asking about.
          bias=1,
          # forgiving yourself is a different question with a different answer, and so is the
          # partner-cheating afterwards one (after-affair, in family.py), which owns the affair
          # words: this card is about forgiving another person for something done to you
          avoid=("myself", "my self", "for what i did", "for what i said", "i did it",
                 "my fault", "my own fault", "hate myself",
                 # the other worlds that say "forgiving": a plant, a pan, a cut of meat and a
                 # recipe are described as forgiving, and a loan is the one other forgiveness
                 # there is. None of them is a person's debt.
                 "plant", "plants", "houseplant", "houseplants", "garden", "gardening",
                 "recipe", "recipes", "pan", "pans", "saucepan", "meat", "chicken", "steak",
                 "cake", "bread", "pastry", "oven", "loan", "loans", "debt", "debts", "tax",
                 "parking", "fine", "fines", "student",
                 # a partner who cheated has its own afterwards card (after-affair, family.py),
                 # written for the months of rebuilding a relationship, and it is the better
                 # answer to "i cant forgive my husband for cheating"
                 "affair", "affairs", "cheat", "cheated", "cheating", "unfaithful",
                 "slept with")),

    # Forgiving yourself is the other half of the same question and it is not the same answer:
    # "i cant forgive myself for what i did" was a punt ("Thanks for telling me"), and the card
    # for forgiving another person would be wrong for it - there is no debt to drop and nobody
    # to keep at a distance.
    entry("forgive-yourself", ((
        "forgive myself", "forgiving myself", "forgive yourself", "forgiving yourself",
        "forgiveness myself", "cant forgive myself", "can t forgive myself",
        "cannot forgive myself", "never forgive myself", "not forgive myself",
        "let myself off", "forgave myself", "hate myself for", "beat myself up",
    )),
          "Forgiving yourself is not letting it slide: it is saying what you did plainly, making "
          "the amends you can, and then treating the debt as paid instead of re-running the "
          "court case every night. Pick the smallest real repair - the apology, the thing you "
          "would do differently - do it this week, and say privately that the next time you "
          "would act differently. If the same voice keeps going over it months later, that is "
          "worth talking through with someone.",
          bias=1),

    entry("friend-quiet", (("friend", "friends", "mate", "bestie"),
                           ("ignoring", "quiet", "not replying", "replying", "replied",
                            "not answered", "hasn t replied", "stopped replying", "distant",
                            "gone quiet", "no reply",
                            # the same silence said as talking: "my friend isn t talking to me"
                            # was being sent "pick one regular thing and go every week" - the
                            # how-to-meet-people answer - and "i havent heard from my friend in
                            # weeks" got nothing at all
                            "isn t talking to me", "isnt talking to me", "not talking to me",
                            "wont talk to me", "won t talk to me", "stopped talking to me",
                            "isn t speaking to me", "isnt speaking to me", "not speaking to me",
                            "wont speak to me", "won t speak to me", "stopped speaking to me",
                            "havent heard from", "haven t heard from", "not heard from",
                            "no word from", "gone silent", "blanked me", "blocked me",
                            "has blocked me", "avoiding me", "off with me",
                            # the same silence said as texting: "my mate hasnt text me back in a
                            # week" was answered "Got it. Is there anything you'd like a hand
                            # with?" and "my friend isnt texting me back" with a three-line
                            # template for asking for something. Every phrase here is a silence,
                            # not a reply - "my friend texted back finally" is a different row.
                            "text me back", "texted me back", "text back", "texted back",
                            "hasnt text", "havent text", "havent texted", "not texted",
                            "not text back", "no text back", "not texting", "stopped messaging",
                            "not messaged")),
          "Ask once, plainly and without accusation: 'I haven't heard from you in a while — are you "
          "okay?' Then give it time. People go quiet for their own reasons, and one warm message "
          "beats three worried ones.",
          # a friend gone quiet over money they owe is the money question, not this one
          avoid=("lent", "lend", "borrowed", "owes", "owe", "paid me back", "pay me back",
                 "money", "quid", "pounds", "tenner", "fiver", "deposit"),
          # "i ignored my friend all week" is the person doing the ignoring: the message above
          # asks somebody else why they went quiet, and there is nobody to send it to. A deed of
          # their own stands the row down and the repair answers it (bot/compose/repair.py).
          guard=lambda reading: not owns_the_deed(reading)),
    entry("ask-whats-wrong",
          (("ask her", "ask him", "ask them", "what s wrong", "whats wrong",
            "what do i say", "should i say", "what to say",
            "ask what", "ask if", "how to ask", "how do i ask"),
           ("friend", "annoyed", "upset", "off with me", "big thing", "row", "distant",
            "ignoring me", "isn t talking", "seems off")),
          "Make it a question about them, not an accusation: 'You seem a bit off with me \u2014 have I "
          "done something?' Say it once, in person or on the phone, not in a long message. If they "
          "say nothing is wrong, believe them and carry on normally; people often need a day before "
          "they can say it.",
          # "how do I bring it up" is raising a problem (wording.raise-a-problem-with-friend),
          # not asking a friend what is wrong, and the two must not compete for the line
          # grief and bad news belong to the conversation lane, not to a friend being off with you
          avoid=("died", "death", "passed away", "funeral", "grief", "bereave", "cancer",
                 "miscarriage", "hospital", "griev", "loss", "lost her job", "lost his job", "lost her mum",
                 "lost his dad", "fired", "redundant", "laid off", "lend", "borrow", "pay rise",
                 "promotion", "owe", "pay back", "pay it back", "money", "pounds", "quid",
                 "back", "cant pay", "can t pay", "bring it up", "brought it up", "broach",
                 "mention", "mentions", "raise it", "ruining",
                 # a follow-up about food is still about the food, even when the earlier
                 # line said "my friend": "her cooking is bad" then "so what do i say"
                 "cook", "cooking", "cooked", "bake", "baking", "food", "meal", "dish",
                 "recipe", "pastry",
                 # a partner or a child is not a friend, and a row that keeps repeating is a
                 # different question from "why is she off with me"
                 "turns into a row", "turns into an argument", "turns into a fight",
                 "always ends in", "partner", "husband", "wife", "boyfriend", "girlfriend",
                 "my mum", "my mother", "my dad", "my father", "my son", "my daughter",
                 "my kids", "the kids",
                 # a birthday one of them missed is family.py's question, both directions
                 "birthday", "forgot", "forgotten", "missed",
                 # a friend who cancelled is family.py's pattern question, not "why is she off"
                 "cancel", "cancelled", "canceled", "cancels", "cancelling", "bailed",
                 "let me down", "no show",
                 # asking a friend for space is not asking them what is wrong with you: the
                 # words "ask" and "friend" are the same, the question is the other way round
                 "space", "some space", "need space", "some room"),
          # "i ignored my friend all week, what do i say" is their own deed, and the script above
          # is what to ask the other person about theirs (bot/compose/repair.py).
          guard=lambda reading: not owns_the_deed(reading)),
    # Introducing two people who do not know each other: "how do i introduce two friends" was a
    # shrug, and it is a script question, so it belongs with the other social ones.
    entry("introduce-friends",
          (("introduce", "introducing", "introduction", "introduce them", "introduce two"),
           ("friends", "friend", "friends who", "people", "each other", "two friends", "them",
            "how", "best", "awkward", "what do i say", "say")),
          "Give each one a reason to be pleased to meet the other - \"Sam, this is Priya, she runs "
          "the same ridiculous hill route as you\" - and then give them something to do with each "
          "other, even a question you are also part of. Say a little about what each does so nobody "
          "has to audition, and stay for the first few minutes rather than leaving them alone.",
          # introducing yourself is a different script from introducing two other people, and
          # "introduce myself at a new job" was taking this one
          avoid=("myself", "me to", "yourself", "introduce me",
                 # and so is introducing a baby to an older child, a pet to a dog or a cat to a
                 # resident cat: "how do i introduce a new baby to a toddler" was told to say a
                 # nice thing about each of them to the other.
                 "baby", "babies", "newborn", "toddler", "toddlers", "sibling", "siblings",
                 "puppy", "puppies", "kitten", "kittens", "new dog", "new cat", "resident dog",
                 "resident cat", "to the dog", "to the cat", "to our dog", "to our cat",
                 # The audience words ("kids", "children", "son", "parents", "partner") are NOT
                 # here. Fencing them took the good answer off "how do i introduce my boyfriend
                 # to my kids" - main gave "give each one a reason to be pleased to meet the
                 # other", and the line then fell to meeting-the-new-baby, which offered the
                 # scan picture. A partner introduced to children is still two people being
                 # introduced; the baby row fences the partner in its own avoid instead.
                 "stepchild",
                 # Two animals being introduced are the pets lane's question, and the singular
                 # words were missing: "how do i introduce two dogs" was read as two people and
                 # told to give each one a reason to be pleased to meet the other ("Sam, this is
                 # Priya, she runs the same hill route as you"), which is nobody's dog. Only the
                 # shapes that name an animal as the thing introduced are fenced, so a plan that
                 # mentions a dog in passing ("introduce my new partner to my friends at the
                 # dog park") keeps the two-people script.
                 "a dog", "the dog", "our dog", "my dog", "two dogs", "dogs to", "my dogs",
                 "our dogs", "the dogs", "a cat", "the cat", "our cat", "my cat", "two cats",
                 "cats to", "my cats", "our cats", "the cats", "a puppy", "two puppies",
                 "a rabbit", "the rabbits", "my rabbit", "a guinea pig", "a hamster",
                 "a budgie", "a parrot", "a horse", "a pony", "two pets",
                 # "a new pet to my kids" is a real question and none of the pet cards answers it
                 # yet, so the bare word "pet" stays out of the fence: a wrong two-people script
                 # is what it gets today, and a punt would be no better. The animal names above
                 # are what the cards can answer.
                 )),
    entry("better-listener",
          (("listener", "listen better", "listen well", "listening", "listen properly",
            "a better listener", "good listener", "bad listener", "interrupt", "interrupts",
            "interrupting", "talk over", "talks over"),
           ("how", "better", "be", "become", "am i", "do i", "advice", "tips", "learn",
            "he says", "she says", "they say", "people say", "says i")),
          "Stop preparing your reply while they are still talking: most of us are half a sentence "
          "ahead, and people can hear it. Then say back what you heard in one line - \"so the "
          "meeting went badly and your boss blamed you\" - before you offer anything, and ask one "
          "follow-up question instead of topping up with your own story. Sit still and leave a "
          "second of silence after they stop; that gap is usually where the real thing gets said.",
          # a quiet friend, a row and a hearing problem are other questions
          avoid=("hearing", "hearing aid", "deaf", "ear", "tinnitus", "quiet", "ignoring",
                 "not replying", "podcast", "audiobook", "music", "radio", "tv", "speaker",
                 "headphones", "eavesdrop", "neighbour", "neighbor", "landlord",
                 # "my friend talks over me" is a thing to raise with them, not tips for the
                 # person doing the talking; the telling script is wording's
                 # a day full of interruptions is the office's problem, not a listening habit:
                 # "I get interrupted every five minutes at work, how do I get anything done"
                 # was getting the listen-better answer
                 # "how do i stop my phone listening to me" is a privacy question about a
                 # device, not about being better at listening to people
                 "my friend talks over me", "over me", "cuts me off", "cut me off",
                 "interrupts me", "interrupting me", "keeps interrupting", "talks over my",
                 "every five minutes", "all day", "anything done", "get anything done",
                 "open plan", "open-plan", "phone",
                 "iphone", "android", "alexa", "echo", "siri", "microphone", "ads", "adverts",
                 "spying", "recording", "listening to me", "google home")),

    entry("text-after-date",
          # A call is the same question as a text, and "how long should i wait before calling
          # after a date" was the dried fruit keeping row (the fruit and the date with a person
          # are one word once the keeping row has the date words). The verb is in the key here,
          # and the date in the second part is what keeps "call the vet" out of it.
          (("text", "texting", "text back", "texted", "message", "reply",
            # the phrase, not the bare verb: "how long should i wait to call" names nobody and
            # is as often a plumber as a date, and the wait words below are its whole second
            # part. "calling after a date" says which one it is.
            "call after", "calling after", "phone after", "phoning after", "ring after"),
           ("first date", "after a date", "after the date", "a date", "dating", "matched",
            "tinder", "hinge", "bumble", "how long should i wait", "wait before")),
          "Text the same evening or the next morning. There is no waiting rule worth playing, and "
          "a day of silence reads as disinterest rather than mystery. Say something specific - "
          "'still thinking about that story about the ferry' - and end with a question or a plan, "
          "so it is easy to answer in one line. If nothing comes back, one follow-up after a few "
          "days is fine and then leave it: no reply is a reply.",
          avoid=("my ex", "my mum", "my dad", "boss", "work", "landlord", "doctor", "school",
                 "girlfriend", "boyfriend", "wife", "husband", "bank")),    # Cheering someone up, comforting someone and "what do i say to a friend who is sad" are one
    # question. It reached a shrug, or - because the first group alone is the ask - the "have I
    # done something?" script, which is the opposite advice. The person and the low mood are the
    # second and third parts, so a line that names neither still gets nothing from here.
    entry("cheer-someone-up",
          (("cheer up", "cheered up", "cheering up", "cheer him up", "cheer her up",
            "cheer them up", "cheer my",
            # the pronoun sits in the middle of the commonest phrasing, so "cheer up" as a run
            # of words misses "how do i cheer someone up", which hedged on main
            "cheer someone up", "cheer somebody up", "cheer a friend up", "cheer up someone",
            "cheer up a friend", "cheer up my", "cheer their",
            "comfort", "comforting", "console", "consoling",
            "feel better", "feel any better", "make them feel", "make her feel", "make him feel",
            "do something nice for", "something nice for", "what can i do for",
            # "what should i say" is how people ask for the words, and it sits in `ask` below:
            # in the key it scored a person's name on its own ("what should i say to my
            # neighbour about the noise" and "what do i say to my gp about feeling low" were both
            # sent this advice), because two of the three groups scoring is enough.
            ),
           ("friend", "best friend", "mate", "bestie", "mum", "mother", "mam", "dad",
            "father", "parent", "parents", "sister", "brother", "partner", "husband",
            "wife", "boyfriend", "girlfriend", "son", "daughter", "child", "someone",
            "him", "her", "them", "person", "somebody", "colleague", "neighbour", "neighbor"),
           ("sad", "sadness", "down", "low", "upset", "unhappy", "miserable", "struggling",
            "rough time", "hard time", "bad time", "going through", "crying", "cried",
            "cheer up", "comfort", "bad news", "having a hard", "not themselves",
            "in a rut", "stressed")),
          "Small and specific beats big and vague. Send one message today saying you have been "
          "thinking of them, then offer a fixed thing: \"I'll bring dinner on Thursday\" or \"walk "
          "on Sunday?\" rather than \"let me know if you need anything\". Ask whether they want "
          "company or quiet before you turn up, and do not tell them to cheer up - being told to "
          "feel better is the one thing that never works.",
          # Being asked to help is not the same as being asked what to say. Without this, the
          # person and "struggling" were enough on their own, and "my mum is 80 and struggling on
          # her own, how do i get her some help" was sent the cheer-up script instead of the care
          # assessment. A line about someone's hard time still counts ("going through a rough
          # time"), because the advice is the same advice.
          ask=("cheer up", "cheered up", "cheering up", "cheer him up", "cheer her up",
               "cheer them up", "cheer my", "cheer someone up", "cheer somebody up",
               "cheer a friend up", "cheer up someone", "cheer up a friend", "cheer up my",
               "comfort", "comforting", "console", "consoling",
               "feel better", "feel any better", "make them feel", "make her feel",
               "make him feel", "do something nice for", "something nice for", "what can i do for",
               "what do i say", "what can i say", "what should i say",
               "rough time", "hard time", "bad time", "going through", "having a hard time"),
          avoid=("died", "death", "passed away", "funeral", "grief", "bereave", "burial",
                 "cancer", "miscarriage", "hospital", "diagnosis", "suicide", "killed",
                 # a landmark birthday is a plan, not a low mood: "my nan is 80 what can we do
                 # for her birthday" was reaching this row on "what can we do for"
                 "birthday", "birthdays", "80th", "70th", "90th", "anniversary", "retirement",
                 # someone who has lost a person is the grief question (loss.py, friends'
                 # "what do i say to someone who lost their dad"), not the cheer-up one
                 "lost", "loss", "losing", "gone", "widow", "widowed", "ill", "sick",
                 "hospice", "carer", "grieving", "grieves", "grieved", "bereavement",
                 # a friend who is off with you is ask-whats-wrong's question, not this one
                 "angry", "annoyed", "off with me", "row", "argument", "falling out",
                 "furious", "ignoring me", "ignores me", "owes", "owe", "borrow", "lent",
                 "money", "pay back", "birthday", "forgot",
                 # a gift or a present is the shopping question
                 "gift", "present", "presents", "buy", "buying", "what should i get",
                 "christmas", "anniversary"),
          guard=_not_a_plain_gesture),
    # The help-asking shapes: "how do i help a crying friend", "my friend is having a hard time
    # how can i help", "how do i help my partner who is stressed", "my friend is depressed what
    # do i do". The cheer-up row above needs a cheer word in the line; these lines do not have
    # one, and the answer is the same advice.
    entry("help-someone-through", (HELPING_ASK, HELPING_PERSON),
          ("Be there before you fix anything: say the plain thing - \"that's really hard, I'm "
           "sorry\" - and then ask what they need today, company or quiet. A fixed offer helps "
           "more than an open one (\"I'll bring dinner on Thursday\", \"walk on Sunday?\"), and "
           "the message tomorrow, when the first day's fuss has died down, is the one they "
           "remember. If it has been weeks and they have stopped seeing anyone or stopped "
           "eating, say so plainly and help them book a GP appointment."),
          # the loneliness row beside it also names the person, and "my friend is depressed
          # what can i do" is the friend question rather than the make-friends one
          ask=HELPING_TROUBLE, bias=1,
          # the person and the trouble are both needed, and the trouble is in `ask`: without it
          # "how do i help my son with his reading" and "how do i help my wife with the
          # housework" were read as a friend in trouble.
          avoid=("reading", "homework", "maths", "math", "spelling", "revision", "exam",
                 # "my friend seems depressed what do i do" is the notice-it-and-ask row: the
                 # line has already spotted something, and one plain question is the answer
                 "seem", "seems", "seemed", "acting", "noticed", "notice",
                 # the asker is the one in the wrong or the one feeling it: "i let my mum down,
                 # what do i do" is a question about their own guilt, not about helping her
                 "let", "letting", "feel", "feels", "feeling", "felt", "guilt", "guilty",
                 "housework", "cleaning", "bins", "move house", "moving house", "downsize",
                 "job", "cv", "benefits", "allowance", "dementia", "phone", "laptop", "wifi",
                 "barking", "diet", "weight", "paperwork", "tax", "passport", "bins",
                 # what to say to someone who has lost a person is the loss row's answer, and
                 # the grief one is the grief module's
                 "suicide", "funeral", "eulogy", "miscarriage")),
    # A promise made and then dreaded is not a request for advice on the job itself: "i told my
    # mate id help him move but i dont want to" reached the fussy-child card, because `help` and
    # `him` are its keys and the want rule stood in for its ask. The question is how to get out
    # of it, so the answer starts with saying it early rather than with the move.
    entry("a-favour-i-said-yes-to",
          (("said id", "said i would", "said i'd", "said i will", "promised", "agreed",
            "agreed to", "volunteered", "offered to", "said yes", "said yes to",
            "said yes when",
            # the promise is often written "id help" rather than "I'd help"; a bare "id" keeps
            # that shape without taking "told my wife I don't want to move", which is a
            # conversation between two people, not a favour to get out of
            "id"),
           ("help", "favour", "favor", "move", "moving", "lift", "babysit", "babysitting",
            "childcare", "paint", "decorate", "drive", "collect", "pick up", "house sit",
            "dog sit", "fix")),
          "Say it early, before they plan around you: \"I'm sorry - I said I'd help, but I'm not "
          "going to be able to.\" You don't owe a detailed reason; if you want to soften it, offer "
          "something smaller you can still do (\"I can drop the keys round on Friday\"). Don't "
          "leave it to the last minute, and don't say yes again to be kind - a clear no "
          "now is easier on them than a no then.",
          ask=("dont want", "don't want", "not want", "cant face", "can't face", "couldnt face",
               "couldn't face", "regret", "dreading", "dread", "rather not", "changed my mind",
               "wish i hadnt", "wish i hadn't", "no longer want", "dont fancy", "don't fancy"),
          # a work task somebody agreed to is the say-no-at-work question, not a favour between
          # friends, and the office row has the script for it
          avoid=("boss", "manager", "colleague", "work", "job", "office", "client", "shift",
                 "overtime", "meeting", "deadline"),
          bias=1),
    entry("meet-parents", (("parents", "family"), ("partner", "meet", "meeting", "first time")),
          "Take something small for the house, ask them questions about themselves, and don't try "
          "to impress — be interested and easy. Offer to help with the washing up; it's the "
          "cheapest way to be liked.",
          # "the parents" in the line is not always a meeting: somebody cooking for their
          # partner's parents is asking what to put on the table, and the advice to take
          # something round to the house is for the visit, not for the dinner being made.
          guard=_not_cooking_for_them),
    entry("ask-someone-out",
          (("ask out", "asking out", "asked out", "ask her out", "ask him out", "ask them out",
            "ask a girl out", "ask a boy out", "ask a guy out", "ask a lad out", "ask a man out",
            "ask the guy out", "ask the girl out", "ask someone out", "ask out my crush",
            "ask my crush out", "ask her on a date", "ask him on a date", "on a date",
            "out on a date", "first date",
            # the phrases only: `lookup._forms("chickening")` includes the bare "chicken", so one
            # loose form here reads the meat as the nerve and "how do i make chicken stock" got
            # this row. "chicken out", "chickening out" and "chickened out" keep their own forms.
            "chicken out", "chickening out", "chickened out", "get cold feet",
            "want to ask out", "want to ask her out", "want to ask him out",
            # "how do i talk to a girl i like" is the invitation question, and no ask word in it
            # put it here: it was reaching the goodbye row. The shape names both the person and
            # the liking, so it cannot be a stranger or a meat line.
            "talk to a girl i like", "talk to a boy i like", "talk to a guy i like",
            "someone i like", "somebody i like"),
           ("how", "should", "do i", "help", "nervous", "scared", "terrified", "chance",
            "way", "best", "do it", "pluck up", "brave",
            # "im too shy to ask her out" says the whole question and has no ask word in it:
            # it was reaching the echo filler ("You're too shy to ask her out, good to know").
            "shy", "too shy", "shyness", "embarrassed",
            # the line most people actually type is a want and a block, with no "how do i" in
            # it at all: "i want to ask out my crush but i keep chickening out" is the same
            # question as "how do i ask her out", and it was reaching the raw chicken instead
            "want", "wants", "wanted", "keep", "keeps", "kept", "cant", "can't", "cannot",
            "afraid", "frightened",
            # "i chickened out of asking her out" is the whole question and carries no ask word
            # from the list above, so the person being asked is the second half here. It needs
            # the object: "i chickened out" on its own is as likely to be a dentist, and
            # "i chickened out of asking for a raise" is work, so neither reaches this row.
            "ask her", "ask him", "ask them", "asking her", "asking him", "asking them",
            "ask someone", "ask a girl", "ask a boy", "ask a guy", "crush", "out with",
            "on a date", "first date")),
          "Make it a small, specific invitation rather than a confession: \"I like talking to you - "
          "do you fancy a coffee on Saturday?\" Name a day and a thing, ask in person or in one "
          "short message, then leave it with them - the answer is theirs to give. A no is "
          "information, not a verdict: \"no worries, see you Thursday\", said warmly and meant, is "
          "what keeps the friendship. The only real mistake is the speeches.",
          ask=("how", "should", "do i", "what", "way", "best", "nervous", "scared",
               "chance", "help", "brave", "shy", "too shy", "shyness", "embarrassed",
               # "chicken" on its own is the meat: "how do i tell when the chicken is done" was
               # reaching this row on the bare "how". Only the nervous phrase counts.
               "want", "wants", "wanted", "chicken out", "chickening out", "chickened out"),
          # a first-date outfit, a wedding date and "how long do I wait before texting after a
          # first date" are other questions: the last one is about messages, not the invitation
          avoid=("wear", "wearing", "outfit", "clothes", "dress", "shoes", "hair",
                 "restaurant", "wedding", "tax return", "use by", "best before", "expired",
                 "out of date", "throw out",
                 # the meat is not the nerve: "how do i tell when the chicken is done" and
                 # "how do i stop raw chicken going off" are cooking, not asking anyone out
                 "done", "cooked", "cook", "cooking", "raw", "oven", "roast", "roasting",
                 "juices", "thermometer", "thaw", "defrost", "fridge", "freezer", "meat",
                 "temperature", "left out", "gone off",
                 # "chicken out" is a phrase in the key above, and the matcher counts its words
                 # one at a time: any cooking line with "chicken" in it that also carries a "how"
                 # or a "keep" was buying the invitation speech. "how do i spatchcock a chicken",
                 # "how do i make chicken soup", "how do i marinate chicken" and "how do i keep
                 # chicken from drying out" were all told to ask her out over a coffee. A word
                 # that names the meat or the job is the cooking sense, so any of these stands
                 # the row down and the cooking rows keep the line.
                 "spatchcock", "joint", "jointing", "butterfly", "soup", "stock", "carcass",
                 "bone", "bones", "boneless", "skin", "skinless", "breast", "breasts",
                 "thigh", "thighs", "drumstick", "drumsticks", "wing", "wings", "nuggets",
                 "marinade", "marinated", "marinating", "marinate", "rub", "brine", "brining",
                 "drying out", "dry out", "dries out", "juicy", "tender",
                 # the fridge question, in the words people use for it: "how do i keep chicken
                 # fresh" was still the invitation, and "chicken fresh" cannot be said of a person
                 "chicken fresh", "meat fresh", "keep it fresh", "keep them fresh",
                 "keep food fresh", "chicken in the fridge", "chicken in the freezer",
                 "poach", "poaching", "boil", "boiling", "grill", "grilling", "bake", "baking",
                 "barbecue", "bbq", "air fryer", "slow cooker", "curry", "tikka", "kebab",
                 "casserole", "traybake", "pie", "gravy", "stuffing", "sandwich", "wrap",
                 "salad", "pasta", "rice", "noodles", "stir fry", "stir-fry",
                 "text", "texts", "texting", "message", "messages", "messaging", "reply",
                 "replies", "wait", "how long", "chase", "ghosted",
                 # a first date is the occasion, not the thing asked for: "whats a nice song for
                 # a first date" asked for a song and got the invitation speech, and so would a
                 # film, a playlist or a present. A line that names the thing it wants is that
                 # thing's question, so this row stands down for it and the music, film and
                 # present rows keep the line.
                 "song", "songs", "playlist", "playlists", "tune", "tunes", "album", "albums",
                 "music", "band", "bands", "film", "films", "movie", "movies", "series",
                 "podcast", "podcasts", "book", "books", "novel", "poem", "poems", "quote",
                 "quotes", "gift", "gifts", "present", "presents",
                 # "keep" is in this row's key words for "i keep chickening out", and with it a
                 # dish kept the way it should be came here: "how do i keep chicken warm", "how
                 # do i keep the chicken moist" and "how do i keep my chicken tender" all got the
                 # ask-her-out answer on the word "keep" plus the bird. A quality asked for is a
                 # pan question, and it is never a nerve.
                 # "i keep forgetting to take the chicken out" is the bird going from the
                 # freezer to the counter, and the key above counts "chicken" and "out" one word
                 # at a time: with "keep" also in the key this row won the line and answered a
                 # freezer question with a speech about asking someone out. The bird as the
                 # object of a taking is the kitchen, however the person says it.
                 "take the chicken out", "take a chicken out", "get the chicken out",
                 "taking the chicken out", "the chicken out of", "forgot to take",
                 "forget to take", "forgetting to take",
                 ) + KEEP_QUALITY_WORDS),

    entry("friend-busy",
          (("friend", "friends", "friendship", "mate", "mates", "friendships"),
           ("busy", "no time", "hard to keep", "keep in touch", "drifted", "drift", "drifted apart",
            "lost touch", "losing touch", "catch up", "see each other", "distance",
            "long distance", "kids", "work")),
          "Stop waiting for a free evening and put a small, regular thing in the diary instead: a "
          "twenty-minute call every second Sunday, or a walk at the same time each month. Say why "
          "you are doing it - 'I miss you, and I am bad at this, so I am booking us in' lands "
          "better than a vague let's catch up. Voice notes between times keep the thread alive, "
          "and doing one small favour beats a grand plan you both cancel.",
          ask=("busy", "time", "keep", "touch", "drifted", "drift", "lost", "losing", "catch up",
               "see each other", "distance"),
          # a friend gone quiet, a friend who owes money and meeting the parents are other lines
          avoid=("ignoring", "quiet", "not replying", "owes", "owe", "lent", "money", "parents",
                 "partner", "wedding", "argument", "fell out",
                 # a friend who has died is grief, not a diary problem. "keep going" used to be in
                 # the key above, and with "friend" in the first part it took every line about a
                 # loss, including the ones a memory-carried word pushed here.
                 "died", "dies", "dying", "death", "dead", "passed away", "passing", "funeral",
                 "buried", "burial", "killed", "kill", "suicide", "grief", "grieving", "loss",
                 "lost him", "lost her", "lost them", "miss him", "miss her", "miss them",
                 # the illness words stay out: a friend who is ill is exactly who a small
                 # regular thing in the diary is for, and a bereavement turn is already caught
                 # by "keep going over" and the death words above
                 "keep going over", "going over",
                 "over the last", "cant stop thinking", "can't stop thinking")),
    # Getting out of a conversation without hurting anyone, which is asked often enough and had no
    # answer: it is a social skill with a shape, not a fact.
    # The other half of a chat: keeping one going. "How do i keep a conversation going" was read
    # as how to end one, because the exit row keys on the word "conversation" plus "how do i" and
    # any question about a chat carries both. It is a different skill with a different answer.
    entry("keep-a-conversation-going",
          (("conversation", "chat", "small talk", "talking", "talk", "chatting",
            "nothing to say", "things to say", "silences", "silence", "stranger", "strangers"),
           ("keep going", "keep it going", "keep a conversation going", "keep a chat going",
            "keep the chat going", "keep chatting", "keep talking", "chat going", "going", "start",
            "starting", "starter", "starters", "open", "opening", "awkward", "silence",
            "nothing to say", "run out of things", "run out of", "dries up", "stalls",
            "stranger", "strangers", "someone new", "new people", "new person", "ice breaker",
            "icebreaker")),
          "Ask about the answer you just got instead of starting a new subject - \"how did that "
          "go?\" or \"what was the best bit?\" - because a conversation usually dies from "
          "answering and moving on, not from having nothing to say. Give a little of yourself so "
          "it is not an interview, and when the talk stalls offer something to look at or do: the "
          "weather lasts a line, a photo, a menu or a dog lasts ten minutes.",
          # the exit, the argument, a friend gone quiet and the app's own group chat are other
          # lines, and an interview is a different kind of talking
          avoid=("end", "ending", "ends", "finish", "finishing", "leave", "leaving", "get out of",
                 "escape", "goodbye", "politely", "polite", "excuse myself", "job interview",
                 "interview", "row", "argument", "argue", "fell out", "ignoring", "break up",
                 "group chat", "unsubscribe", "mute",
                 # "im dying to see that film everyone keeps talking about" is somebody saying
                 # what they want to watch: the film, the queue and the person's own enthusiasm
                 # are not a hunt for things to say, and with the first-line guard standing
                 # down this row answered it (jade-easel on #5548)
                 "dying to", "everyone keeps", "film", "films", "movie", "movies", "series",
                 "binge", "episode", "episodes", "telly", "netflix",
                 # a person who talks over you is a complaint about them, not a hunt for
                 # something to say: "my colleague keeps talking over me" read the words "talking"
                 # and "keeps" as keeping a chat going and answered "ask about the answer you
                 # just got instead of starting a new subject". The behaviour phrases are what
                 # separate them, so they stand this row down and work.py's difficult-colleague
                 # keeps the line.
                 "over me", "talks over", "talking over", "talked over",
                 "interrupts me", "interrupting me", "interrupt me", "interrupted me",
                 "ignores me", "ignoring me", "undermines me", "undermining me",
                 "shouts at me", "shouting at me", "yells at me", "yelling at me",
                 "takes credit", "taking credit")),
    entry("end-a-conversation-leave",
          (("conversation", "chat", "talking", "talk", "nattering", "small talk",
            "phone call", "call with", "speaking to", "chatting",
            # the exit named as the whole ask: "how do i leave a party politely" never says
            # "conversation", so the phrases have to reach the first group to score at all
            "leave a party", "leave the party", "leaving a party", "leave early",
            "leaving early", "end a conversation", "end the conversation", "end a chat",
            "exit a conversation", "get out of a conversation", "slip away", "bow out",
            "say goodbye", "get off the phone", "getting off the phone", "get off a call",
            "get off this call",
            # the article varies and the phrase has to be contiguous to match: "how do i get
            # off a phone call" and "how do i get off the call" both scored nothing at all
            "get off a phone call", "get off the call", "get off the call politely",
            "off a phone call"),
           ("end", "ends", "ending", "finish", "finishing", "politely", "polite", "get away",
            "get out of", "escape", "leave", "leaving", "stop", "stuck", "wont stop", "won't stop",
            # "get off" is how most people say it about a phone: the phrase "get off the phone"
            # sat in the first group with no word to pair with, so the row could not score
            # "how do i get off the phone" at all and the line got a punter.
            "get off", "getting off", "hang up", "hanging up", "ring off",
            # "how do i" and "how to" are not here on purpose: the shape of a question scored a
            # phrase on every line ever typed, so "how do i talk to my partner about money" and
            # "how do i talk to my boss about a raise" matched on "talk" alone and got the
            # goodbye instead of the telling script. The exits above all name the ending itself.
            "gracefully", "excuse myself", "end it", "cut it short",
            "wrap it up",
            # the exit itself, named as a phrase: a party or a chat is closed the same way, and
            # the phrases keep "how do i plan a dinner party" and "how do i arrange a party" out
            # "leave early" and "leaving early" were here for a party, and they carried a line
            # on their own with no conversation in it: "i need to leave early today" was told how
            # to close a chat gracefully. A party exit is said with the party ("leave a party",
            # "slip away") and leaving work early is wording.asking-for-time-off's question.
            "leave a party", "leave the party", "leaving a party",
            "slip away", "slipping away", "end a chat", "end the chat", "end a conversation",
            "end the conversation", "exit a conversation", "get out of a conversation",
            "make my excuses", "bow out", "say goodbye", "get going"),
           # A phrase alone scores 3, under MIN_SCORE, so the exit is also read word by word:
           # "how do i say goodbye" and "make my excuses" are the same question as "end a chat".
           # These words need the conversation part above to reach two matched words, which keeps
           # "how do i leave a job" and "how do i leave my boyfriend" out.
           ("goodbye", "goodbyes", "bye", "excuses", "early", "slip away", "bow out",
            "head off", "go home", "get going", "sign off",
            # "how do i end a chat at a party" said the ending as "end", which sat only in the
            # phrase "end a chat" in the group above - and a phrase on its own scores 3, under
            # the minimum. The ask below still needs a conversation, a party or a call in the
            # line, so "how do i end my tenancy early" and "how do i end a contract" stay out.
            "end", "ends", "ending")),
          "Close it with a reason and a warm line rather than fading out: name the thing you have "
          "to get to, say one true thing about the conversation, then go. \"I'm going to have to "
          "head off - I'm so glad you told me about the job\" or \"Right, I'd better get on, but "
          "it was good to catch up.\" Give the reason first, because people hear the reason as "
          "respect, and keep it about the time rather than the person. If someone is mid-ramble, "
          "wait for a full stop and step in with their name; if you are on the phone, stand up and "
          "say you have to go. End with something that opens the next time - \"next week?\", "
          "\"text me when you hear\" - so it reads as a pause and not a brush-off.",
          # The exit words below are not enough on their own: "end" plus "early" is two matched
          # words, and the shape of the ask ("how do i") is a phrase that scored 3 on most lines
          # ever typed. So "how do i end a tenancy early", "how do i end my lease early" and
          # "how do i cancel my broadband early" were all answered with a warm line about ending a
          # chat. What makes the line this entry's is the thing being left - a conversation, a
          # party, a call - so one of those has to be in it.
          ask=("conversation", "conversations", "chat", "chats", "chatting", "talk", "talking",
               "small talk", "nattering", "phone", "call", "calls", "speaking to", "party",
               "parties", "goodbye", "goodbyes", "bye", "excuses", "bow out", "slip away",
               "head off", "go home", "get going", "sign off", "visit", "guests", "guest"),
          # an argument, a friend gone quiet, a call that will not end and a breakup are other
          # lines
          # the fence wording.end-a-conversation keeps, and the same reason: "how do i stop
          # talking in class" got this row off the words "stop talking", and a script for getting
          # off the phone is not an answer about a classroom.
          # "how do you say goodbye in irish" is the phrasebook's line: the word goodbye is the
          # only thing in it that looks like a conversation ending, and the language stands the
          # exit down so the phrase table answers instead.
          guard=lambda understood: not said_in_a_language(understood),
          avoid=TALKING_IS_NOT_A_CHAT + (
                 "spanish", "espanol", "español", "french", "francais", "français", "italian",
                 "german", "deutsch", "welsh", "cymraeg", "irish", "gaeilge", "gaelic",
                 "translate", "translation", "what does",
                 "argument", "argue", "row", "fell out", "ignoring", "not replying", "quiet",
                 # overthinking a chat afterwards is not leaving one: "how do i stop overthinking
                 # conversations" was told to close it with a reason and a warm line, which
                 # answers a person who is still in the room. The overthinking card has the words.
                 "overthinking", "overthink", "over thinking", "replaying", "replay",
                 "going round in my head", "goes round in my head", "dwell", "dwelling",
                 "ruminating", "ruminate", "cant stop thinking", "can't stop thinking",
                 # a person who has stopped speaking to you is not a conversation you are trying
                 # to leave: "my sister stopped speaking to me" matched "speaking to" above and
                 # was told to close it with a reason and a warm line. The silence shapes stand
                 # this row down, so the row that says how to break the silence answers instead.
                 "stopped speaking to me", "stopped talking to me", "stopped texting me",
                 "isnt speaking to me", "isn t speaking to me", "isnt talking to me",
                 "isn t talking to me", "wont speak to me", "won t speak to me",
                 "wont talk to me", "won t talk to me", "havent spoken to me",
                 "haven t spoken to me", "hasnt spoken to me", "not speaking to me",
                 "not talking to me", "not on speaking terms",

                 # a party has its own exit script (the host, the one-line reason), and the
                 # party goodbye is `leave-a-party`'s line: "how do i say goodbye at a party"
                 # was told how to join a group, so the party words stand this card down and
                 # that row picks the line up
                 "party", "parties", "a do", "gathering", "drinks", "dinner", "barbecue",
                 "bbq", "celebration", "host", "night out", "leaving do",
                 "break up", "breakup", "broke up", "dumped", "divorce", "dating", "date",
                 "flirting", "crush", "shy", "nervous", "anxious", "bad caller",
                 # "how do i talk to a girl i like" is asking someone out, and this card is for
                 # getting out of a chat that is already running
                 "a girl i like", "a boy i like", "someone i like", "somebody i like",
                 "ask her out", "ask him out", "ask them out", "fancy", "fancies",
                 # and a talk about feelings, or about money, is not a chat that is ending:
                 # both were sent "close it with a reason and a warm line"
                 "feelings", "my feelings", "emotions", "how i feel", "money", "parents",
                 "my parents", "his parents", "her parents",
                 "cold caller", "scam", "voicemail", "email", "letter", "text", "message",
                 "wrong number", "job", "shift", "hospital", "country", "flat", "house",
                 "tenant", "landlord",
                 # "how do i say goodbye in greek" is a translation, and "say goodbye" is in
                 # this row's key: a language named in the line stands the exit script down so
                 # the phrase card (study.py, say-language) answers it.
                 "in spanish", "in french", "in italian", "in german", "in portuguese",
                 "in greek", "in turkish", "in welsh", "in japanese", "in chinese",
                 "in mandarin", "in dutch", "in polish", "in russian", "in arabic",
                 "translate", "translation",
                 # Raising a subject with someone you live with is the opposite of leaving a
                 # chat, and every exit word is in the line: "how do i talk to my son about
                 # puberty" and "... my daughter about periods" were both answered with the
                 # warm line about ending a conversation. The shape is what says which it is.
                 "talk to my son about", "talk to my daughter about", "talk to my child about",
                 "talk to my kid about", "talk to my children about", "talk to my kids about",
                 "talk to my teenager about", "talk to my boy about", "talk to my girl about",
                 "speak to my son about", "speak to my daughter about",
                 "talk to him about", "talk to her about", "talk to them about",
                 # "leave early from work" is a holiday request, not a chat that is ending
                 "work", "office", "school", "term", "annual leave", "time off", "holidays",
                 # "work" stands this entry down but its compounds do not: "how do i talk to my
                 # boss about my workload" matched "talk" and "how do i" and got the goodbye.
                 # A workload is a thing to raise with somebody, never a chat to get out of.
                 "workload", "workloads", "workloads of", "my workload",
                 # "leave a group chat" is the app's Exit group button, and the group chat
                 # answers own it: a group, a mute or a notification setting is not a person.
                 "group chat", "group message", "group conversation", "whatsapp", "telegram",
                 "signal", "messenger", "instagram", "facebook", "the group", "group",
                 "leave the group", "exit group", "unsubscribe", "mute", "muted",
                 "notifications",
                 # "how do i keep a conversation going" is the opposite question: the exit row
                 # keyed on "conversation" and "how do i" and answered it with how to leave.
                 "keep going", "keep it going", "keep a conversation going",
                 "keep the conversation going", "keep talking", "nothing to say",
                 "run out of things", "awkward silence", "small talk", "conversation starter",
                 "start a conversation", "start the conversation", "keep a chat going",
                 "keep the chat going", "keep chatting", "chat going", "stranger", "strangers",
                 "someone new", "new people", "nothing to say", "things to say",
                 "say no", "saying no", "say yes", "no without", "without sounding",
                 "sounding like", "turn down", "turn them down", "refuse",
                 # "keep a conversation going" is the opposite question, and it has its own row
                 # in wording.py now: this card is for the person who wants out, not the one who
                 # wants in.
                 "keep a conversation going", "keep the conversation going", "keep talking",
                 "keep a chat going", "keep the chat going", "start a conversation",
                 "start the conversation", "conversation starter", "things to say",
                 "nothing to say", "make conversation", "talk to people", "talk to anyone",
                 "small talk", "make small talk", "making small talk", "mingle", "mingling",
                 "networking", "networking event", "know nobody", "knows nobody",
                 # a party has its own exit script (the host, the one-line reason),
                 # and "how do i leave a party politely" is that script, not this one
                 "party", "parties", "a do", "gathering", "drinks", "dinner",
                 # No bare "party"/"parties"/"a do" here. They used to stand this card down for
                 # every party line, and with the party words also in the subject half that
                 # silenced the card on its own question: "how do i say goodbye at a party" then
                 # went to whatever else matched. The ask gate above still wants an exit word, so
                 # "how do i plan a party" and "how do i arrange a party" never reach this card.
                 # the card is for a chat that has run dry too: "how do i handle awkward
                 # silences" is the opposite of leaving one
                 "awkward silences", "silences",
                 # a hard conversation to have is not a chat to close, and `hard-conversation`
                 # below outranks this card on the lines that name it, so only the ones that
                 # ask how to START are fenced here: "how do i end a difficult conversation"
                 # keeps this card, because the ask is the exit.
                 "start a difficult", "start the difficult", "start a hard", "start a awkward",
                 "have a difficult conversation", "have a hard conversation",
                 "have the difficult conversation", "handle a difficult conversation",
                 "handle a hard conversation", "bring up a difficult conversation",
                 "bring up a hard conversation",
                 "confront", "confronting", "confrontation",
                 "have it out", "bring it up"), bias=1),
    # "Make my excuses and leave" names the exit with no chat, party or call in the line. The
    # phrase sat only in the second group of end-a-conversation-leave (the doing words), so the
    # first part was empty and the whole line reached nothing; adding it to the first group
    # there also sent "my excuses are rubbish" and "excuse myself from a wedding" to the chat
    # script. So the phrase is its own row, gated on an asking shape and stood down by the
    # places, events and people that already own their own exit.
    entry("make-my-excuses",
          (("make my excuses", "made my excuses", "making my excuses"),
           ("leave", "leaving", "go", "going", "head off", "get away", "slip away", "exit")),
          "Close it with a reason and a warm line rather than fading out: name the thing you have "
          "to get to, say one true thing about the time, then go. \"I'm going to have to head "
          "off - I'm so glad we got to talk\" or \"I'd better get on, but it was really good to "
          "catch up.\" Have your reason ready in one line because the next question is always "
          "why, and don't apologise twice; leaving when you said you would is kinder than "
          "drifting about waiting for a gap.",
          ask=("how do i", "how to", "what do i say", "what should i say", "what can i say",
               "ways to", "way to"),
          # A party, a wedding, a meeting or a call has its own exit, and a statement about
          # oneself is not an ask for words: "my excuses are rubbish" is not this card's line.
          avoid=("party", "parties", "a do", "gathering", "drinks", "dinner", "barbecue",
                 "bbq", "celebration", "night out", "wedding", "funeral", "meeting",
                 "interview", "date", "phone", "call", "calls", "work", "office", "school",
                 "boss", "landlord", "customer", "client", "because i", "for being late",
                 "are rubbish", "always", "never")),
    # The conversation nobody wants to start. Asked most about a sister, a friend or a partner,
    # and the only answer in the tree for it was the one about ending a chat.
    entry("hard-conversation",
          (("difficult conversation", "hard conversation", "awkward conversation",
            "tricky conversation", "uncomfortable conversation", "have it out",
            "bring something up", "bring it up", "confront", "confronting", "confrontation",
            # "how do i tell my husband how i feel" is the same ask and was reaching the
            # wording fallback, so the feeling itself is keyed and the person comes from the
            # second part.
            "tell them how i feel", "tell her how i feel", "tell him how i feel",
            "how i feel", "say how i feel", "how i really feel",
            # "how do i talk about my feelings" and "how do i open up about my feelings" name
            # the same conversation and were reaching the stranger-opener row, which told them
            # to ask the person about the queue. The noun forms belong with the verb ones.
            "feelings", "my feelings", "emotions", "my emotions", "open up", "opening up",
            "share my feelings", "share how i feel"),
           ("how", "do i", "should", "can", "what", "start", "handle", "say", "tell", "approach",
            "friend", "friends", "mate", "sister", "brother", "partner", "husband", "wife",
            "boyfriend", "girlfriend", "mum", "dad", "mother", "father", "flatmate", "someone",
            "about something", "nervous", "dread", "awkward")),
          "Ask for ten minutes at a calm time, then say it in one sentence with one example: "
          "\"when you cancelled on Friday it felt like I didn't matter\" lands, while \"you "
          "always cancel\" starts a fight. Say what you want to change rather than what they did "
          "wrong, let them answer once without interrupting, and finish by agreeing what happens "
          "next time.",
          # ending a chat, a row already going and a work matter are other answers, and asking
          # for the words is the wording fallback's turn.
          # "how do i end a difficult conversation" is the exit question, not the start of one:
          # the bare verb has to be fenced too, or naming the talk pulls it back here.
          avoid=("end a conversation", "end the conversation", "end a chat", "leave a party",
                 # "how do i stop feeling dizzy when i stand up" is a body question: "feeling"
                 # is the hard-talk row's "how i feel", so a symptom word stands it down
                 "dizzy", "dizziness", "light headed", "lightheaded", "faint", "fainting",
                 "nauseous", "nausea", "vomit", "sick", "queasy", "shaky", "weak",
                 "breathless", "short of breath", "chest pain", "palpitations", "pins and needles",
                 "headache", "headaches", "migraine", "sore", "ache", "aching", "pain", "hurts",
                 "hurt", "tired", "exhausted", "sleepy", "bloated", "constipated", "itchy",
                 "rash", "cramp", "cramps", "swollen", "numb", "stiff", "stressed", "anxious",
                 "low", "down", "depressed", "nervous about the", "panic",
                 # overthinking a chat afterwards is not leaving one: "how do i stop overthinking
                 # conversations" was told to close it with a reason and a warm line, which
                 # answers a person still in the room. The overthinking card owns those words.
                 "overthinking", "overthink", "over thinking", "replaying", "replay",
                 "going round in my head", "goes round in my head", "in my head",
                 "dwell", "dwelling", "ruminating", "ruminate", "cant stop thinking",
                 "can't stop thinking", "keep thinking about",
                 # a feeling about food is the eating card, not a talk with a person: "how do i
                 # stop feeling guilty about food" was told to ask for ten minutes at a calm time
                 "food", "eating", "ate", "meal", "meals", "diet", "weight", "calories",
                 "guilty about food", "guilt about food", "binge", "bingeing",
                 # being tired all the time is the health card's: "how do i stop feeling tired
                 # all the time" was told to ask for ten minutes at a calm time
                 "tired", "exhausted", "exhausting", "no energy", "always sleepy", "sleepy",
                 "fatigue", "fatigued", "worn out", "run down", "lethargic",
                 "say goodbye", "leave early", "get away", "politely",
                 # the exit verb itself: "how do i end a difficult conversation" is the same
                 # question as "how do i end a chat", and the exit card keys that shape
                 "end", "ends", "ending", "finish", "finishing", "get out of", "excuse myself",
                 "bow out", "walk away", "cut it short", "stop talking", "wind it up",
                 "argument", "argue", "row", "shouting", "fell out", "not talking",
                 "appraisal", "pay rise", "redundancy", "resign", "dismissal", "grievance",
                 "word it", "what do i say", "what should i say", "draft", "email", "text",
                 "message",
                 # a line with feelings for someone is the invitation row, not the hard talk:
                 # "i have feelings for my flatmate" matched the person in the second group
                 "for him", "for her", "for them", "have feelings", "caught feelings",
                 "in love", "crush", "attracted"),
          # "i hurt my husbands feelings" is not a conversation they are working up to having: the
          # hurt is theirs to mend, and the script above is the one for raising a complaint of
          # their own. A deed of the speaker's own stands the row down (bot/compose/repair.py).
          guard=_names_a_person_and_is_not_a_deed),
    # "how do i refuse wine politely" and "how do i not drink at a wedding" were shrugs, and
    # "i dont drink but people keep buying me drinks" was the 24-hour rule for impulse buying -
    # advice for the person doing the spending, given to the one being bought for. The four-word
    # refusal exists in the say-no rows, which answer the first asking; this is the row for the
    # second and third asking, which is the part people are stuck on.
    # "how do i set boundaries with my partner" and "with my flatmate" were a search hedge
    # each, and "my partner does not respect my boundaries" was the echo of its own words: the
    # rows that answer a parent who rings too often (`parent-needs-space`) or a child who will
    # not listen are keyed on those people, so an adult telling you what to do had no row.
    entry("say-where-the-line-is",
          (("boundaries", "boundary", "set limits", "limits with", "clear limits", "limits on",
            "draw the line", "the line is", "put my foot down", "stand up for myself",
            "stand up to", "keeps doing it", "does not respect", "doesnt respect",
            "wont respect", "won't respect", "walks all over", "takes advantage"),
           ("partner", "husband", "wife", "boyfriend", "girlfriend", "fiance", "fiancee",
            "flatmate", "flat mate", "housemate", "roommate", "friend", "friends", "mate",
            "sister", "brother", "sibling", "colleague", "coworker", "co worker", "brother in law",
            "sister in law", "in law", "in laws", "family", "someone", "him", "her", "them",
            "people")),
          ("Name the one thing, in a sentence, and say what you will do rather than what they "
           "must stop: \"I'm not lending money again\" lands where \"you take advantage of me\" "
           "starts a fight. Pick the boundary that matters most this week, say it once when "
           "nothing is being argued about, and expect to say it twice before it holds. Then keep "
           "the consequence yourself - a limit nobody follows through on is a suggestion - and "
           "let the smaller stuff go, because five boundaries kept beat twenty announced."),
          bias=1,
          # A parent, a child, a boss and a landlord are other rows: `parent-needs-space`,
          # `telling-a-child-off`, the work-hours card and the tenancy one each know their
          # person, and a line that names one of them is that row's question.
          avoid=("mum", "mother", "dad", "father", "parents", "parent", "stepmum", "stepdad",
                 "nana", "gran", "grandma", "grandad", "mother in law", "mother-in-law",
                 "child", "children", "kid", "kids", "son", "daughter", "toddler", "teenager",
                 "baby", "boss", "manager", "landlord", "tenant", "neighbour", "neighbor",
                 "dog", "cat", "sleep", "bedtime", "rent", "money", "deposit", "contract",
                 "work hours", "overtime", "nights")),
    entry("turn-down-a-drink",
          # The refusal is named with its object. A bare "say no" plus an occasion word made
          # every invitation a drink - "how do i say no to a wedding invite", "can i say no to a
          # birthday party", "how do i say no to a hen do" all went from the family entry to the
          # lime-and-soda script - so the phrases here are the ones that name a drink or a
          # person's buying, and nothing else in the row has to carry that job.
          (("refuse a drink", "refuse a glass", "refuse wine", "refuse alcohol", "refuse booze",
            "refuse another", "refuse the drink", "refuse drinks", "refusing a drink",
            "turn down a drink", "turn down a glass", "turn down drinks",
            "turned down a drink", "turning down a drink",
            "say no to a drink", "say no to drinks", "say no to alcohol", "say no to wine",
            "say no to the drink", "say no to another drink", "say no to booze",
            "saying no to a drink", "decline a drink", "decline the drink", "decline drinks",
            "declining a drink",
            # not the bare "i dont drink": that is a statement about them, and the row answered
            # it with a script for a question they had not asked. The lines that need it name
            # the buying or the occasion as well.
            "not drink at", "not drink when", "not drink with", "not drink and",
            "not drink in front", "not drinking",
            "without drinking", "avoid drinking", "stopped drinking", "giving up drinking",
            "non drinker", "non-drinker", "teetotal", "sober", "keep buying me",
            "keeps buying me", "keeps buying", "buying me", "buys me", "buy me"),
           ("drink", "drinks", "drinking", "wine", "beer", "pint", "pints", "shot",
            "shots", "alcohol", "booze", "lager", "cider", "prosecco", "cocktail",
            "cocktails", "spirits", "vodka", "gin", "whisky", "whiskey", "a round",
            "rounds", "glass", "pub", "party", "wedding", "christening", "after work",
            "work do", "night out", "hen do", "stag do", "meal", "dinner")),
          "Have the line ready before the glass arrives: 'Not for me, thanks - I'm on the lime "
          "and soda.' Four words, said with a smile, and then ask them something, because a "
          "reason at a table is an invitation to be talked round. Keep a soft drink in your hand "
          "- people top up a full glass far less - and if a round lands in front of you anyway, "
          "leave it or pass it on rather than argue. When someone presses, use the same sentence "
          "again, then name it once, quietly and only to them: 'I don't drink - it's boring, but "
          "it's easier if you don't buy me one.' Two no's from the same person is not rude; it is "
          "what stops the third.",
          # a line about cutting down or about somebody else's drinking is the health answer,
          # and the shop is the spending one: those rows keep their own lines
          avoid=("how much", "how many units", "units", "cut down", "cutting down", "reduce",
                 "give up", "quit", "stopping", "stop drinking", "withdrawal", "shakes",
                 "liver", "alcoholic", "alcoholism", "dependent", "addiction", "help me stop",
                 "am i drinking", "too much", "my husband", "my wife", "my partner", "my dad",
                 "my mum", "my son", "my daughter", "my friend drinks", "buy a", "buying a",
                 "cheapest", "price of", "calories", "syns", "units in",
                 # a refusal at a table is often about food, and a person who is left out of
                 # the round is asking about that, not about what to say: both keep their rows.
                 # "meal" and "dinner" left the keys for the same reason - they are not about
                 # alcohol, and "how do i say no to pudding at dinner" is a pudding question.
                 # a pet who has stopped drinking is a vet question, not a refusal at a table:
                 # "my cat is not drinking" was reaching the pub script while "my cat isnt
                 # drinking" already had the pet answer one word away.
                 "my cat", "my dog", "my pet", "my puppy", "my kitten", "cat is", "dog is",
                 "cat has", "dog has", "cat wont", "dog wont", "kitten", "puppy", "vet",
                 "hamster", "rabbit", "guinea pig", "parrot", "fish tank", "litter tray",
                 # and nor is a horse, a pony or livestock: "my horse is not drinking" was given
                 # the script for refusing a glass at a party.
                 "horse", "horses", "pony", "ponies", "donkey", "donkeys", "goat", "goats",
                 "sheep", "cow", "cows", "livestock", "stable", "trough",
                 # and the small ones, for the same reason: "my rat is not drinking" and "my mice
                 # are not drinking" reached this script too.
                 "rat", "rats", "mouse", "mice", "gerbil", "gerbils", "degu", "degus",
                 "chinchilla", "chinchillas", "ferret", "ferrets", "hedgehog", "hedgehogs",
                 "budgie", "budgies", "tortoise", "tortoises", "lizard", "snake",
                 "pudding", "puddings", "dessert", "desserts", "cake", "cakes", "seconds",
                 "second helping", "another helping", "a helping of", "portion", "food",
                 "chips", "sweets", "chocolate", "biscuits", "left out", "left behind",
                 "chips", "sweets", "chocolate", "biscuits", "left out", "left behind",
                 "excluded", "everyone else", "second helping", "another helping",
                 # a host's invitation is a different question from a glass pressed on you, and
                 # "how do i say no to a wedding invite" is the family entry's: the occasion
                 # words stay in the keys (an entry from a domain the talk has not touched is
                 # stood down), so the shapes that are an invitation are refused here instead
                 "invite", "invited", "invitation", "invitations", "bridesmaid", "wedding day",
                 "stag", "hen party",
                 # "how do i refuse a glass of water" is the hydration answer, and "glass" or
                 # "refuse" alone is not a drink: the alcohol has to be named somewhere.
                 "water", "hydrat",
                 "excluded", "the only one not", "everyone else"),
          bias=1),
]

# Turning someone down after a date had no row: the refusal script is for a request for your time
# ("I can't take that on this week"), which is the wrong thing entirely for a person who has just
# asked you out. The phrases name the date, so an ordinary "no" keeps the row it had.
ENTRIES += [
    # Ignoring someone politely is not the same question as ending a chat: "how do i ignore
    # someone without being rude" and "how do i avoid someone politely" were both a hedge, and the
    # ending card's "name the thing you have to get to" is the wrong advice for a person you have
    # to keep seeing. The answer is boring rather than absent, so it has its own card.
    entry("polite-distance",
          # The verb alone is not the question: "how do i avoid getting sick on a plane", "how do
          # i avoid injury when running" and "how do i avoid a hangover" are the cards for those
          # things, and a bare "avoid" in this key took all seven of them. Every phrase here ends
          # in a person - someone, a neighbour, a colleague - so only a person is kept at a
          # distance.
          (("ignore someone", "ignoring someone", "ignore him", "ignore her", "ignore them",
            "avoid someone", "avoiding someone", "avoid him", "avoid her", "avoid them",
            "avoid a neighbour", "avoid my neighbour", "avoid a colleague", "avoid my colleague",
            "avoid my in laws", "avoid my in-laws", "avoid a person", "dodge someone",
            "dodge a neighbour", "dodge my neighbour", "dodge him", "dodge her", "dodging him",
            "brush off", "brush them off", "brush him off", "brush her off", "sidestep someone",
            "evade someone", "get away from someone", "keep someone at arm", "at arms length"),
           ("rude", "politely", "polite", "without being", "nicely", "discreetly", "kindly",
            "how do i", "how to", "without upsetting", "at work", "neighbour", "neighbor",
            "colleague", "in law", "in laws", "someone")),
          "Don't blank them - be brief, dull and busy, which is easier to keep up than avoidance "
          "and gives them nothing to push against. Answer in a sentence, ask nothing back, do not "
          "laugh at the jokes, and keep your hands occupied or your coat on. \"I can't stop, I'm "
          "just heading in\" works every time, and stepping away while you say it ends the "
          "exchange. If it is someone you cannot move away from, sit at the end of the row and "
          "arrive a minute late rather than making a thing of it.",
          avoid=("ignore my", "ignore him", "ignore the", "ignoring my", "text", "message",
                 "call", "email", "notification", "warning light", "error", "dog", "baby",
                 "toddler", "child", "customer complaint", "ignore a",
                 # a question is dodged, not a person: "how do i sidestep a question politely"
                 # was answered with how to keep a bore at arm's length
                 "question", "questions", "answering", "answering the")),
    # the id is not `decline-a-date`: family.py has a row of that name since the dating questions
    # were done again there, and two rows with one id make the registry ambiguous. Both stand:
    # that one wins the plainest wording, this one the "not interested", "no spark" and "one date"
    # forms.
    entry("decline-a-date-kindly",
          (("second date", "third date", "another date", "asked me out again",
            "dont want to see them again", "don't want to see them again",
            "dont want to see him again", "don't want to see him again",
            "dont want to see her again", "don't want to see her again",
            "see them again", "tell someone i dont want", "tell them i dont want",
            "ask me out again", "asked me out", "asks me out", "wants to meet again",
            "wants to see me again", "wants a second date", "dont want a second date",
            "don't want a second date", "turn him down", "turn her down", "turn them down",
            "let him down", "let her down", "let them down", "end it after one date",
            "after the first date", "had one date", "went on one date", "one date and",
            "not interested in him", "not interested in her", "not interested in them",
            "no spark", "no chemistry", "didnt feel a spark", "didn't feel a spark"),
           ("nicely", "polite", "politely", "without hurting", "without being mean", "not mean",
            "how", "what do i say", "what should i say", "what to say", "words", "text",
            "message", "reply", "respond", "ghost", "ghosting", "ignore", "badly", "kind")),
          ("Say it plainly, kindly and early - a text the same evening or the next day is not "
           "rude, and leaving it unanswered is: \"I enjoyed meeting you, but I'm not feeling a "
           "romantic connection, so I don't want to lead you on.\" Keep it about you rather than "
           "about them, because \"you're not my type\" invites an argument and \"no spark\" does "
           "not. No long explanation, no apology for the feeling, and no offer of friendship you "
           "do not mean. Then do not reply to the pushback."),
          ask=("how", "what", "say", "said", "saying", "text", "message", "reply", "words",
               "nicely", "polite", "politely", "him", "her", "them", "someone")),
]

# The bot's own trust question, which no card owned: a person asks the shortest version of "can
# I rely on what you tell me" and got the search hedge. It is a yes/no question, and the honest
# answer is yes for everyday things with the limit said plainly, because a chatbot can be wrong.
ENTRIES.append(entry(
    "bot-can-i-trust-you",
    (("trust", "trusts", "rely on", "count on"),
     ("you", "u", "chatbot", "bot", "your advice", "your answer", "your judgement",
      "your judgment", "this chatbot")),
    "Yes, for everyday questions: I give you my best answer and say when I am not sure. Check "
    "anything that matters - a diagnosis, money, a legal deadline - with someone qualified, "
    "because I can be wrong.",
    ask=("trust", "rely on", "count on"),
    avoid=("trust fund", "trust him", "trust her", "trust them", "trustworthy", "trust a",
           "trust my", "trust the", "trust it")))

# "can you keep a secret" is the same privacy question in a yes/no shape, and it fell to the search
# hedge. The answer is yes for this chat and no promise beyond it: nothing is written down and
# nothing carries over, which is the honest version of keeping a confidence.
ENTRIES.append(entry(
    "bot-keeps-a-secret",
    (("keep", "keeps", "keeping", "hold"),
     ("secret", "secrets", "between us", "to yourself")),
    "Yes - it stays in this chat. Nothing is written down and nothing carries over, so nobody "
    "else reads it and it is gone when we finish. If it is something a person needs to act on, "
    "though, tell someone who can.",
    ask=("you", "your", "u", "can i", "could i", "will you", "would you"),
    avoid=("surprise", "surprises", "birthday", "present", "gift", "keep it from", "keeping it from")))
# --- a phrase people use about their own life ---------------------------------------------
# "what is a midlife crisis" was a search hedge. It is not a fact so much as a word people are
# handed, so the answer says what it means and then what to do with it. ("what is a boundary"
# was the same shape and is answered by the limits row above, so there is no second row here.)
ENTRIES.append(
    entry("midlife-crisis",
          (("midlife crisis", "mid-life crisis", "middle age crisis", "mid life crisis",
            "midlife", "middle aged", "middle age"),
           ("what is", "whats", "what does", "mean", "am i having", "having one", "signs",
            "symptoms", "why", "when", "age", "cope", "deal with", "husband", "wife", "partner",
            "mum", "dad", "he", "she", "my", "feel")),
          ("A midlife crisis is the shake-up people often have roughly between 40 and 55, when "
           "the shape of a life stops matching the person in it and the changes come in a rush: a "
           "new car, a sudden hobby, a job left, a marriage questioned. It is not an illness and "
           "it is not inevitable - the research says most people's wellbeing rises through midlife "
           "- but the sense of time running out is real, and it is usually about mortality rather "
           "than about youth. The useful move is to name what is actually missing (freedom, "
           "friendship, a body that works, work that matters) and change that one thing rather "
           "than the whole life at once."),
          avoid=("menopause", "perimenopause", "hot flushes", "period", "hormone", "testosterone",
                 "birthday", "40th", "50th")))
