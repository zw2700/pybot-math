"""A line that reacts to the answer just given: "wow", "really?", "seriously".

A reaction to something the *person* said has its own pools in the composer, and they are right:
"ouch" after a report of a bad day asks what happened. This is the other reaction - the one aimed
at the bot's own answer. "how do i poach an egg" then "wow" got "Alright then — good luck with
it", which closes a conversation the person was opening, and "how do i stop my back aching" then
"really?" got the same, which leaves somebody who doubts the answer still doubting it.

Both are the ack pool's turn today: "wow" and "really" are in its word list, and the pool has no
way to see what they were reacting to. So this module reads only that - the line is nothing but
one of these reactions, and the reply above it was an answer and not a line of the bot's own -
and hands back a reply that answers the answer. It says nothing at all otherwise, which keeps
"wow" after a plan on "Good plan. What sparked it?" and "wow, that is a lot" on its own reading.

Run it alone:

    python -m bot.compose.reaction "wow" --after "Slide it into barely moving water for three."
"""
import re

# Surprise at the answer, and doubt about it, said as a phrase of one to three words. Everything
# else in the line has to be a breather in front of it ("oh wow", "ah really", "no way"), so a
# line that says anything of its own - "wow that is a lot", "really good thanks" - is not this.
PHRASES = {
    "wow": "awe", "woah": "awe", "whoa": "awe", "wowsers": "awe", "wowee": "awe",
    "omg": "awe", "gosh": "awe", "blimey": "awe", "crikey": "awe", "cor": "awe",
    "geez": "awe", "jeez": "awe",
    "really": "doubt", "seriously": "doubt", "honestly": "doubt", "truly": "doubt",
    "surely": "doubt", "no way": "doubt", "for real": "doubt", "get out": "doubt",
    "you what": "doubt", "come on": "doubt", "say what": "doubt", "my word": "awe", "good god": "awe",
    "my god": "awe", "oh my god": "awe", "oh my word": "awe", "good heavens": "awe",
}
# The breathers people put in front of either. None of them is a reaction on its own: a bare "no"
# is a refusal and a bare "sure" is agreement, so neither is read here.
LEAD = frozenset((
    "oh", "ah", "aw", "ooh", "uh", "um", "well", "so", "and", "but", "my", "god", "jesus",
    "christ", "jeez", "geez", "good", "bloody", "damn", "just", "huh", "hmm", "ok", "okay",
    "no", "for", "get", "out", "the", "hell", "heck", "come", "on", "you", "what", "say",
    "yeah", "yes",
))
# What a reaction to an answer sounds like when the answer was one to act on.
AWE_REPLIES = (
    "It sounds like more than it is — the whole thing is usually one step. Which bit do you "
    "want to start with?",
    "It is easier once you have done it once. Do you want that as a list you can follow?",
    "Most of it is one small thing done properly. Shall I say which part matters most?",
    "That is the whole trick of it, honestly. Anything in there you want me to go over?",
)
DOUBT_REPLIES = (
    "Yes, really — and it is the small part that does the work. Which bit do you want me to go "
    "over?",
    "It is true, honestly. Is there a part of it that sounds off to you?",
    "I know it sounds odd — that is the whole answer though. Which bit would you not bet on?",
    "It is right, yes. Which part surprised you?",
)
# An answer that is an emergency answer, a sympathy answer or an honest "I don't know" is not one
# to be taken in or doubted: "wow" over "call an ambulance" has no reply in these pools, and the
# bot's own hedge is not an answer to be surprised by.
# A reaction to a death, a crisis or a hedge is not a reaction to an answer. The sympathy pools do
# not open with "sorry for your loss" as often as they open with "I'm really sorry", so the word
# itself is what stands this down: "my dad died in march" / "wow" was answered "That is the whole
# trick of it, honestly" before this guard read the "sorry" in the line above it.
NO_ANSWER = re.compile(
    r"\b(?:999|911|112|111|ambulance|a&e|casualty|emergency|urgent care|a search|search online|"
    r"rather not guess|sorry|sad news|condolence\w*|passed away|passed on|funeral|grief|"
    r"grieving|bereave\w*|miss (?:him|her|them)|died|death|dying|"
    r"hurt yourself|harm yourself|end your life|crisis|samaritans|suicide|116 123)\b")

# A reaction to an answer about a body - an ache, a lump, a burn - is not a reaction to a set of
# instructions. "my tooth is aching" then "wow" was told "That is the whole trick of it, honestly",
# which is the answer to a recipe; the person is not surprised at a trick, they are taking in
# something about their own body. Both "wow" and "really?" get the same pool here, because what
# they are answering is the same: an answer that says get it seen.
A_CARE_ANSWER = re.compile(
    r"\b(?:gp|doctor|dentist|dental|nurse|pharmac\w*|111|999|a&e|nhs|clinic|"
    r"ring (?:them|us|the)|get it (?:looked at|checked|seen)|needs? (?:looking at|checking|seeing)|"
    r"ache|aching|aches|pain|sore|swelling|swollen|lump|rash|inflamed|fever|bleeding|burn|"
    r"sprain)\b")
# The answer is only half of it: a care answer is one somebody asked about their own body, and the
# words a body answer is made of are the words a recipe is made of too. The deep-frying answer says
# "so the temperature does not drop", and reading the answer alone told a person surprised by
# frying instructions about a medical appointment. So the person's own line has to name a body or a
# symptom - "my tooth", "my back", "my knee" - and the answer above has to be the kind of answer
# that line gets. That is also what keeps a body line from a year ago out of this pool: "i had a
# panic attack last year" then "wow" is not somebody being told to get something looked at now.
# ...and the body has to be one they own: "my back garden is full of weeds" is `back` inside a
# phrase that is not a body at all, and with the lifting card above it ("puts five times the strain
# on your back") the person with weeds was told to get it looked at. Every line this pool is for
# says the body as theirs - "my tooth", "my back", "my stomach", "my eyes" - so the possessive is
# what separates a body word from the same word in a place name.
A_BODY_LINE = re.compile(
    r"\b(?:my|his|her|their|our|your|the left|the right)\s+(?:tooth|teeth|gums?|jaw|back|knee|"
    r"knees|hip|shoulder|neck|throat|chest|stomach|belly|tummy|arm|arms|leg|legs|foot|feet|ankle|"
    r"wrist|hand|hands|finger|fingers|thumb|toe|toes|head|headache|migraine|ear|ears|eye|eyes|"
    r"skin|nose|sinus|lump|rash|itch|itchy|sore|ache|aching|aches|pain|painful|hurt|hurts|"
    r"hurting|swollen|swelling|bleed|bleeding|fever|cough|burn|burning|blister|sprain|sting|"
    r"infection|gland|glands)\b"
    # "my back garden", "my back door", "my back room": `back` is the first word of a place, and
    # the words that follow it are what says so. The lookahead is what keeps the possessive gate
    # from taking a garden for a spine.
    r"(?!\s+(?:garden|yard|door|room|wall|seat|gate|fence|window|path|drive|field|lane|page|"
    r"cover|button|pocket|light|start|of\b))"
    # A body word standing alone as the subject of its own sentence - "tooth ache" as a heading,
    # "head is pounding", "eyes are itchy" - still names a body, so a symptom the line opens with
    # is read too.
    r"|\b(?:toothache|headaches?|migraine|tooth|gums|sore throat|backache|stomach ache)\b")
CARE_REPLIES = (
    "It is worth getting that looked at rather than waiting on it. Anything in there you want "
    "me to go over?",
    "Nothing there is meant to scare you - it is just worth getting it seen. Any part you want "
    "me to say again?",
    "Yes - that one is a ring-them-today sort of thing. Do you want me to say what to ask when "
    "you call?",
    "That is the size of it, honestly. Shall I say what to mention when you get it looked at?",
)


# A judgement asked about the answer above is not a reaction to it either: after the list of £30
# gifts, "do you think thats ok" got the ack pool's "Alright then — good luck with it." — a goodbye
# to the person asking whether they can trust the suggestion. The question is about the bot's own
# answer, so the reply is the bot standing behind it and offering to change the part that does not
# fit, not a sign-off.
# "is that fair" and "does that make sense" are the same check as "is that ok", and they are how
# a plan gets put before somebody out loud. Neither was here, so the reply fell through to the ack
# pool ("is that fair" after a dog and a working day was answered "Sounds good.") or to the search
# hedge ("does that make sense" after a wedding moved to June). The bot's answer to a check is the
# same three things whatever the words are: whether it holds, what would change it, and which part
# is worrying them.
_ASK = (r"(?:ok|okay|alright|fine|sensible|sound|wise|right|fair|"
        r"make\s+(?:any\s+)?sense|worth\s+it|a\s+good\s+idea|"
        r"a\s+good\s+choice|the\s+right\s+(?:thing|way))")
# The line has to end on the judgement: "is that ok for the baby" and "is it ok to train again
# tomorrow" are new questions with an "ok" in them, not somebody looking back at the answer.
_TAIL = r"(?:\s+(?:then|though|honestly|yeah|for\s+me))?\s*[.?!]*\s*$"
CHECK = re.compile(
    r"\b(?:do|would|could)\s+(?:you|u)\s+(?:think|reckon|say|agree)\b[^.?!]{0,24}?\b" + _ASK
    + _TAIL
    + r"|^\s*(?:and\s+|but\s+|so\s+)?(?:is|are|was|were|does|did|would)\s+(?:that|this)\s+"
    r"(?:be\s+|sound\s+|look\s+|seem\s+)?" + _ASK + _TAIL
    + r"|\bare\s+you\s+sure" + _TAIL, re.I)
# ...unless the thing judged is the person's own plan: "im going to quit my job" then "do you
# think thats ok" asks for agreement with a decision that is not the answer above, and "Yes -
# nothing in that is a gamble" would be the bot nodding along with it.
OWN_PLAN = re.compile(
    r"\b(?:i'?m|im|i am|we'?re|were|we are)\s+(?:going|gonna|planning|thinking (?:of|about)|"
    r"intending|about)\b|\b(?:i|we)\s+(?:want|need|have decided|decided)\s+to\b|"
    r"\b(?:i|we)\s+(?:might|may)\s+\w+", re.I)
# ...and the answer above has to be one to stand behind. "I don't know enough to answer that
# honestly. A search should sort you out" is not a judgement anyone can agree with, so a check on
# it is a request for the answer the bot does not have, and the hedge is the honest reply.
NO_STANCE = re.compile(
    r"\b(?:i (?:don't|do not|cannot|can't) (?:know|say)|not know enough|rather not guess|"
    r"a search|search online|look it up)\b", re.I)
# The bot standing behind its own answer. Every line says the judgement and then leaves the door
# open for the detail that would change it, because the one thing this answer cannot know is the
# fact the person has not said yet.
CHECK_REPLIES = (
    "Yes, as far as what you have told me goes - and if a detail is different, the answer changes "
    "with it. Which part are you least sure of?",
    "I would stand by it as advice. What I cannot check is the part only you know - which bit is "
    "worrying you?",
    "It holds up as far as I can tell. Tell me the bit that feels off and I will build the answer "
    "around it.",
    "Yes. It is the answer I would give again, and if one thing in it does not fit your side of "
    "it, say which.",
)


# A line that also asks about the person's own reaction is not a check on the answer: "is that ok
# or am i overreacting" is somebody asking whether their own feeling is allowed, and the composer
# has the warm reply for it ("Not unreasonable at all. How you feel about it is real").
THEIR_REACTION = re.compile(r"\bam i\b|\boverreacting\b|\bbeing (?:silly|daft|mad)\b", re.I)


def _checking(text):
    """Whether the line asks the bot to judge the answer it has just given."""
    said = " ".join(str(text or "").lower().split())
    if THEIR_REACTION.search(said):
        return False
    return bool(CHECK.search(said))


def _bare(text):
    """Which kind of reaction a line that is nothing but a reaction is, or ""."""
    clean = " ".join(str(text or "").lower().replace("\u2019", "'").split())
    clean = clean.strip(" .,!?;:\"'")
    words = re.findall(r"[a-z']+", clean)
    if not words or len(words) > 5:
        return ""
    for size in (3, 2, 1):
        for start in range(0, len(words) - size + 1):
            kind = PHRASES.get(" ".join(words[start:start + size]))
            if not kind:
                continue
            rest = words[:start] + words[start + size:]
            if all(word in LEAD for word in rest):
                return kind
    return ""


def _an_answer(reply):
    """True when the bot's last line was an answer rather than a nod, a question or a hello."""
    line = " ".join(str(reply or "").split())
    if len(line) < 60:
        return False
    if line.endswith("?"):
        return False
    if NO_ANSWER.search(line.lower()):
        return False
    return True


def reply_for(text, memory):
    """The reply to a line that is only a reaction to the answer above, or None."""
    kind = _bare(text)
    if not kind:
        # "do you think thats ok" is five words and a question, so no reaction phrase reads it and
        # the ack pool took it for one. It is not a reaction: it is a check on the answer above.
        kind = "check" if _checking(text) else ""
    if not kind:
        return None
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list) or not turns:
        return None
    last = turns[-1] if isinstance(turns[-1], dict) else {}
    if not _an_answer(last.get("bot")):
        return None
    said = str(last.get("user") or "").lower()
    if kind == "check" and OWN_PLAN.search(said):
        # A judgement asked about the person's own plan is theirs to weigh, not the bot's to stand
        # behind: "im going to quit my job" then "do you think thats ok" is not a check on the
        # answer above, and "I would stand by it" would be the bot agreeing with the decision.
        return None
    if kind == "check":
        # The plan the composer already rules on is not a check on the answer either: after "im
        # hoping to get a promotion", "is that sensible" is answered by the judge pool
        # ("Yes, it makes sense - wanting to get a promotion is a reasonable thing to aim at"),
        # which says the person's own words back; a check reply in its place is the vaguer answer.
        from . import fallback as _fallback
        plan, plan_line = _fallback._the_plan_and_its_line(memory)
        if plan or plan_line:
            return None
    above_text = str(last.get("bot") or "").lower()
    if kind == "check" and NO_STANCE.search(above_text):
        return None
    care = A_BODY_LINE.search(said) and A_CARE_ANSWER.search(above_text)
    if kind == "check" and care:
        # A check on a body answer is a question about the body, not a judgement of the advice:
        # "my knee clicks when i go up stairs" then "is that ok for the baby" is a new worry, and
        # the care pool's "That is the size of it, honestly" answers a reaction it was not asked.
        return None
    if kind == "check":
        pool = CHECK_REPLIES
    elif care:
        # An answer about a body is not an instruction to be doubted: "how do i stop my back
        # aching" then "seriously?" got "Yes, really - and it is the small part that does the
        # work", which doubts a set of steps the bot never gave. Surprise and doubt at an answer
        # like that are both the person taking in something about themselves, and the reply is
        # the same either way.
        pool = CARE_REPLIES
    else:
        pool = AWE_REPLIES if kind == "awe" else DOUBT_REPLIES
    # The same line always gets the same reply, and two people saying the same thing on two
    # different days do not get the same one: the pick comes off the line, the answer it is
    # reacting to and the length of the conversation so far, and never off a clock. The answer has
    # to be in it: "wow" is the whole of what the person said, so a seed without the line above
    # gives every first "wow" in every conversation the same reply, word for word - a stock line,
    # which is the thing this module was written to remove.
    seen = sum(1 for turn in turns if isinstance(turn, dict))
    above = " ".join(str(last.get("bot") or "").lower().split())
    seed = " ".join(str(text or "").lower().split()) + "|" + str(seen) + "|" + above
    index = sum((i + 1) * ord(letter) for i, letter in enumerate(seed)) % len(pool)
    return pool[index]


def main(argv=None):
    import sys
    args = list(sys.argv[1:] if argv is None else argv)
    said = args[0] if args else "wow"
    after = ""
    if "--after" in args:
        rest = args[args.index("--after") + 1:]
        after = rest[0] if rest else ""
    if not after:
        print(_bare(said) or "(nothing)")
        return
    print(reply_for(said, {"turns": [{"user": "", "bot": after}]}) or "(nothing)")


if __name__ == "__main__":
    main()
