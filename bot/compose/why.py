"""The reason behind the answer just given: a bare "why" as a follow-up.

"why", "why not" and "how come" carry no subject of their own, so nothing that matches words on
a line can take them: the knowledge base has no key to match, and the small-talk pools want a
mood, not a question. Main answered them with the search hedge - "I'd rather not guess, a quick
search online will get you a solid answer" - which throws away the turn just given and sends the
person off to look up something they already have half of.

What a friend does with the nudge is say plainly that the reason is not something they can see
from here, and ask the one question that would narrow it. That is all this module says. It never
invents a cause: a confident wrong reason is worse than an honest short one (STYLE.md,
"Honest"), and the thing that would let the bot give a real reason is an entry
in the knowledge base, not a phrase put together here.

Two things have to hold before it speaks. The line has to be the whole question, so a why with
words of its own ("why is my car overheating") goes to whatever can match those words. And the
turn above has to be an answer that made a claim: a condolence, an emergency line, a recall or
the bot's own shrug is not something to ask the reason for, so those keep whatever they would
have said. That is what the module's ANSWERED list is for.
"""
import re

from . import pick
from ..memory import again, another

# The whole line, once tidied: a bare ask for the reason, and nothing else.
BARE_WHY = re.compile(
    r"^(?:(?:but|and|so|ok|okay|yeah|no|well|right)\s+)*"
    r"(?:"
    # "why", "and why", "why not", "why though", "how come"
    r"(?:why|y|how come)"
    r"(?:\s+(?:not|tho|though|so|then|is that|is it|was that|does it|do they|did it|did they|"
    # "why not though", "why not tho": the same question with the same tail two words long, which
    # was left unclaimed and went to the search hedge.
    r"would it|wouldnt it|should i|shouldnt i)(?:\s+(?:tho|though|then))?)?"
    # The same bare ask with the question spelled out: "why did that happen", "why does that
    # happen", "why would that be", "why does it work". It is the identical question in more
    # words, so it goes the same way as "why" instead of to the search hedge. Only the closed
    # set of pronouns and the few verbs people put after them, so a why with a thing of its own
    # ("why did that happen to my car") still carries its own words and keeps its own answer.
    r"(?:\s+(?:did|does|do|is|was|were|would|will|should)\s+"
    r"(?:that|it|this|they|those|these)"
    r"(?:\s+(?:happen|happened|happening|keep happening|keeps happening|work|works|not work|"
    r"never work|be|matter|help|go|goes|go wrong|goes wrong|come|do that|do it))?)?"
    # "how come that happens", "how come it went wrong": the same question with the thing
    # pointed at rather than named, which is still nothing to match words on.
    r"|how come\s+(?:that|it|this)(?:\s+(?:happens?|happened|went wrong|goes wrong|keeps "
    r"happening))?"
    # "what could be causing it", "what is causing this": the cause is asked for by name, and
    # "it" is the thing the answer was about, so the answer above is still the only place to read.
    r"|what(?:'?s|\s+is|\s+was|\s+(?:could|might|would|can|may)\s+be)\s+causing\s+"
    r"(?:that|it|this)"
    # "what am i doing wrong", "what is the problem": the trouble is asked about the same way, and
    # the answer just given is still the only place the reason can come from.
    r"|what(?:'?s|\s+is|\s+was)\s+(?:going wrong|wrong|the (?:problem|issue|matter))"
    r"|what\s+(?:am|are|was|were)\s+(?:i|we)\s+(?:doing\s+wrong|missing|getting\s+wrong)"
    r"|what\s+did\s+(?:i|we)\s+do\s+wrong"
    r")"
    r"[\s?!.,]*$",
    re.IGNORECASE)

# The half of the forms above that asks about the whole answer: "what is causing it", "what could
# be causing that". A "why" ask about a named thing keeps the neutral wording.
CAUSING_IT = re.compile(
    r"what(?:'?s|\s+is|\s+was|\s+(?:could|might|would|can|may)\s+be)\s+causing\s+"
    r"(?:that|it|this)\b",
    re.IGNORECASE)

# "what am i doing wrong" asks what a bare "why" asks - what is behind the trouble - but the
# honest answer is not worded the same: "which part of that do you want the why for?" is a
# question the line has already answered by saying it is all going wrong. The same honesty,
# pointed at the step, and the same refusal to invent a cause (STYLE.md, "Honest").
WRONG = re.compile(
    r"\bwhat(?:'?s|\s+is|\s+was)?\s*(?:am\s+i\s+)?(?:going\s+wrong|wrong|"
    r"doing\s+wrong|getting\s+wrong|missing|the\s+(?:problem|issue|matter))\b"
    r"|\bwhat\s+did\s+(?:i|we)\s+do\s+wrong\b",
    re.IGNORECASE)

# "what did i do wrong" is a fault question about a thing - a loaf, a car, a laptop - and it is a
# question about blame when the thing above it was the person's life. "i lost my job" and "i keep
# shouting at my kids" got "Which part goes wrong - the start, the middle, or the end?" (rose-
# heather, #3685): a process cut into thirds is no answer to either. So the fault wording is only
# used when the answer above was about something that can go wrong - see `_reads_a_fault`.
LIFE = re.compile(
    r"\b(?:my (?:job|work|boss|career|business|kids?|children|son|daughter|mum|mom|dad|husband|"
    r"wife|partner|boyfriend|girlfriend|friend|sister|brother|family|marriage|relationship|"
    r"life|money|salary|wages|benefits|rent|interview|exam|degree|course)|"
    r"job|jobs|jobless|unemployed|redundant|sacked|fired|divorce|divorced|breakup|broke up|"
    r"shouting|shout at|arguing|argued|argument|falling out|fell out|not talking to me|"
    r"grieving|funeral|depressed|anxious|lonely|ashamed|guilty)\b",
    re.IGNORECASE)


def _named_as_a_sentence(last, reason):
    """True when the answer named this very clause as its cause, as "the cause is ..."."""

    want = " ".join(str(reason or "").lower().split()).strip(" .,;:")
    if not want:
        return False
    for sentence in re.split(r"(?<=[.!?])\s+", str((last or {}).get("bot") or "")):
        found = NAMED_CAUSE.search(sentence)
        if not found:
            continue
        clause = " ".join(found.group(1).lower().split()).strip(" .,;:")
        if clause != want:
            continue
        return True
    return False


def _reads_a_fault(last):
    """True when the turn above was about a thing that can go wrong, not about the person's life.

    The fault wording asks which part of the process goes wrong, so it needs a process: a loaf,
    a boiler, a laptop, a washing machine. A line about a job, a row with a friend or a funeral
    is not one, and the honest reply there is the shrug that asks what happened.
    """
    said = " ".join(str((last or {}).get("bot") or "").lower().split())
    them = " ".join(str((last or {}).get("user") or "").lower().split())
    if LIFE.search(them):
        return False
    return bool(said)


# "why not" asks about a choice or a refusal rather than about a thing happening, and the useful
# next thing to say is different: what is stopping it, and what did the other side say.
WHY_NOT = re.compile(r"\bnot\b", re.IGNORECASE)

# "why not" is one shape with two questions in it, and only the person's own line says which.
# After the bot has recommended something ("try couch to 5k", "cut the coffee out after 2pm") the
# question is about the bot's own advice: "why not [have it another way]?" An answer that asks
# about somebody else's motives there invents a person - main asked "What is their side of it?"
# to a person who had only asked why not. It is about a third party only when the person's own
# last line named one deciding something ("my boss said i cant work from home").
THEIR_DECISION = re.compile(
    r"\b(?:he|she|they|him|her|them|his|their|"
    r"my (?:boss|manager|landlord|landlady|wife|husband|partner|boyfriend|girlfriend|ex|mum|mom|"
    r"mam|dad|father|mother|son|daughter|child|kid|friend|mate|neighbour|neighbor|colleague|"
    r"council|company|employer|school|teacher|gp|doctor|nurse|worker|agent|insurer)\b|"
    r"the (?:council|company|school|landlord|manager|boss|insurer|bank|hospital|surgery)\b)",
    re.IGNORECASE)
SAID_NO = re.compile(
    r"\b(?:said|says|saying|told|tells|refused|refuses|refusing|won'?t|wont|will not|"
    r"can'?t|cant|cannot|denied|rejected|decided|decides|reckons|thinks|banned|stopped|"
    r"turned (?:me|it|us) down|not allowed|no chance)\b",
    re.IGNORECASE)


def _about_someone_elses_decision(memory):
    """True when the person's own last line was about somebody else deciding or refusing.

    Read on their line rather than the bot's, because the bot's last line is the advice the "why
    not" is asking about. Only their line can say whether there is another party in the question.
    """
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list):
        return False
    for last in reversed(turns[-3:]):
        if not isinstance(last, dict):
            continue
        # The line the "why not" hangs on can be a bare follow-up of its own ("what can i do"),
        # so the whole window is read and the newest line about a person deciding wins.
        said = str(last.get("user") or "")
        if not said:
            continue
        low = " ".join(said.lower().split())
        if THEIR_DECISION.search(low) and SAID_NO.search(low):
            return True
    return False

# The other half of a "why not": whose advice it was. A person who said the advice themselves
# ("i cant sleep" / "you could try cutting out coffee after 2pm") and then asked "why not" is
# asking the bot to stand behind their own suggestion, and the answer to that is that it is the
# version that works for most people. When the bot recommended the thing ("should i buy an
# electric car" / "yes, because it is cheaper to run") the same "why not" is asking for the
# counter-argument, and there the honest reply is what is stopping it, not a justification of a
# suggestion nobody made. Read on the person's own lines, because the bot's last line is an
# answer to whichever of the two they wrote.
THEIR_SUGGESTION = re.compile(
    r"\A(?:you (?:could|should|might|may|can) (?:try|just|also)|try|maybe try|have you tried"
    r"|why don'?t you|what about|how about|consider)\b"
    r"|\b(?:you (?:could|should|might) (?:try|also try)|have you tried)\b", re.IGNORECASE)
# A bare instruction is a suggestion too ("try couch to 5k", "bleed the radiators first", "feed it
# twice a day"). Only the verbs a person uses to hand on advice, and only at the start of a line:
# "i cut out coffee" is a report, not a suggestion.
SUGGESTED_VERBS = frozenset((
    "try", "cut", "stop", "quit", "feed", "turn", "bleed", "top", "add", "start", "use", "take",
    "buy", "get", "give", "keep", "put", "run", "walk", "drink", "eat", "avoid", "ask", "go",
    "see", "check", "swap", "replace", "wash", "clean", "sort", "leave", "make", "do",
))


def _the_suggestion_was_theirs(memory):
    """True when the person's own line handed on the advice the "why not" is asking about."""
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list):
        return False
    for last in reversed(turns[-3:]):
        if not isinstance(last, dict):
            continue
        said = str(last.get("user") or "")
        if not said:
            continue
        low = " ".join(said.lower().split())
        if THEIR_SUGGESTION.search(low):
            return True
        words = low.strip(" .,!?:;").split()
        if words and words[0].strip(".,!?:;") in SUGGESTED_VERBS:
            return True
    return False


# The modules whose last reply made a claim someone can ask the reason for. A knowledge answer
# and a small-talk line about how they feel both do ("why" after "that clockwork wake-up is your
# body clock" asks for more of it). Everything else - loss, safety, urgent, a recall of something
# said earlier, the fallback's own hedge - is left to answer as it did.
ANSWERED = frozenset(("answers", "chat"))
# An answer has to have something in it to ask the reason for. "Fair enough." and "Got it." are
# acknowledgements, and "why" after one of those is not a question about the world.
SUBSTANCE = 8
# The bot's own hedge is not an answer, but the answer before it still is. A cause ask the
# knowledge base cannot match ("what could be causing it") gets the search line, and a "why"
# typed on top of that would otherwise get the same search line again. Look through the hedge to
# the answer the person is asking about; stop at anything else, so a condolence or a safety line
# is never taken as the thing to explain.
HEDGED = re.compile(
    r"\b(?:search|searching|beyond what i know|don'?t know enough|not something i can see|"
    r"rather not guess|no way of knowing)\b",
    re.IGNORECASE)

# A body thread is answered in the shape that fits it - when it started, what sets it off -
# because that is what narrows a symptom. Anything else gets the neutral form of the same
# honesty: the reason cannot be seen from here, so say which part they want it for.
WHY_ANSWERED = (
    "I'd be guessing at the reason - the cause is not something I can see from here. Which part "
    "of that do you want the why for?",
    "I don't know why, and I'd rather say so than invent one. What happens just before it goes "
    "wrong?",
    "Honestly the why is the bit I can't tell from this side. Tell me which part you mean and I "
    "will help you work it out.",
)

WHY_BODY = (
    "Honestly, I can't tell you why from here - I'd be guessing. What sets it off?",
    "I don't know the reason, and I'd rather say so than invent one. When did you first notice it?",
    "The why is the part I can't see from what you've told me. What is it like at its worst?",
    "No idea why, honestly. Does it happen at a particular time, or after anything in particular?",
)

# Half the answers that deserve a "why" already said it: "hundreds of different viruses cause
# them, so one after another is normal" is the reason, and telling that person the cause cannot be
# seen from here contradicts the line above. So the answer is read for a stated cause first and
# given back in one clause; only when it names none does the honest shrug come out.
#
# The words that carry the cause are the ones the knowledge entries actually use, not the ones a
# person would write in an essay: "condensation comes from warm wet air hitting cold surfaces",
# "the thin film stops the steam forming", "air scatters the short blue wavelengths". A pattern
# list that only knew `because` missed most of them and put the shrug on top of an answer that had
# already said why.
CAUSE = re.compile(
    r"\b(?:because|since|that'?s why|which is why|that is why|is why|comes? from|caus(?:e|es|ed) by|"
    r"means that|so that|the reason (?:is|was)|scatters?|keeps? \w+ (?:from|off|out)|"
    r"stops? [^.]{0,28}?\b(?:forming|coming|happening|going|building|getting|spreading)|"
    r"is down to|which (?:makes|means|is why)|that'?s what (?:makes|keeps|stops|drives|turns)|"
    r"is what (?:drives|turns|causes|makes|keeps|stops)|"
    # "jam that stays runny has had too little sugar": the answer names the shortage as the
    # cause, which is how most keeping and baking entries explain a fault.
    r"(?:has|have|had|got) (?:too (?:little|much)|not enough)|"
    # "a machine that bangs is almost always an uneven load", "it is nearly always the brew",
    # "background apps are usually it": the answer names the cause as the likely one.
    r"(?:is|are) (?:almost |nearly |usually |normally |often |mostly )+(?:always )?\w|"
    # "the smell lives in bacteria left in the fibres"
    r"live?s? in |breaks? (?:the |it |them )?\w+ into |"
    # "a cake sinks when it's underbaked", "the leaves go yellow when it is overwatered": what
    # the thing does, and the condition it does it in, is the reason said as one clause.
    r"\b(?:sinks?|go(?:es)?|turns?|comes?|happens?|fails?|breaks?|stops?|sticks?|cracks?|"
    r"curdl(?:e|es)|collapses?|dries?|burns?|smells?|tastes?|looks?)\b"
    r"[^.;:]{0,40}?\bwhen\b|"
    # the mechanism said in the passive: "the kneecap being pulled off line by weak or tight
    # muscles", "the cartilage is worn away by ..." - something is doing it, and the answer names it
    r"\b(?:is|are|was|were)\s+[^.;:]{0,40}?\b\w+(?:ed|en)\b[^.;:]{0,20}?\b(?:by|from)\b)",
    re.IGNORECASE)
# A reply that explains, then tells you what to do about it: "...hitting cold surfaces, so
# ventilate instead of adding heat". The clause that carries the cause stops where the advice
# starts, or the reason handed back is a cut-off instruction. The verbs are the step words the
# entries use, kept in one place because a second cut needs them: "...so the fluoride stays on,
# and clean between the teeth once a day" ends the reason at `and` too.
STEP_VERBS = (
    r"(?:ventilate|open|keep|use|take|leave|put|run|wipe|wash|give|avoid|let|get|ask|"
    r"check|try|swap|cover|move|hold|store|cook|drink|eat|sit|add|lower|raise|turn|clean|buy|"
    r"restrict|limit|reduce|cut|change|switch|replace|bin|tip|throw|sort|fit|hire|book|"
    r"pick|start|stop|do|make|go|wear|ring|call|fill|write|read|set|work|stay|carry|"
    r"delete|update|download|install|uninstall|restart|reboot|reinstall|clear|free|"
    r"close|move|rotate|treat|rinse|hoover|vacuum|dust|air|dry|iron|seal|label)")
SO_ADVICE = re.compile(r",? ?so (?=" + STEP_VERBS + r"\b)", re.IGNORECASE)
# A sentence that carries a dose or a schedule is the answer's advice, not its reason: "Twice a
# day for two minutes with a fluoride toothpaste, ... once a day with floss" names how often to do
# the thing, and handed back whole to "why" it is the paragraph the person has just read with a
# frame in front of it. A mechanism sentence has no dose in it ("cold makes tiny muscles pull your
# hairs upright, which traps a layer of air"), so this is where the two part company.
DOSE = re.compile(
    r"\b(?:once|twice|three times|four times|daily|weekly|nightly|every (?:day|week|night|morning)|"
    r"a (?:day|week|night|month)|per (?:day|week|month)|\d+ ?(?:times|minutes|hours|glasses|"
    r"litres|grams|g|mg|mg|ml|degrees|sessions))\b",
    re.IGNORECASE)
# A reason that ends where the next step begins without a `so`: "spit rather than rinse so the
# fluoride stays on, and clean between the teeth". A comma before a bare step verb is the same
# boundary as `so`, and the cause clause stops there.
# `air` is a step verb and a noun, and "sunlight ... and air scatters the short blue wavelengths"
# is the reason itself, so the one word that reads both ways is left out of this cut.
AND_STEP = re.compile(r",? ?and (?=(?!air\b)" + STEP_VERBS + r"\b)", re.IGNORECASE)
# "...stops the steam forming droplets, and it holds for a few days": after the cause comes more
# advice, not more reason.
AND_ADVICE = re.compile(r",? ?(?:and|but) (?:it|they|that|this|you|then|if)\b", re.IGNORECASE)
# A cause that sits inside an instruction is the reason for that instruction, not for the thing
# asked about: "never open the coolant cap while it is hot, because it will scald you" answers
# "why" after "my car is overheating" with a reason about the cap. Only the first sentence may
# carry an instruction; anything later has to be explanation all the way through.
# "never open the coolant cap ... because it will scald you" is the reason for not doing the
# thing, not the reason for the thing asked about.
NEGATIVE = re.compile(r"\b(?:never|don'?t|do not|avoid|no need to|there'?s no need)\b",
                      re.IGNORECASE)
# "if it overheats again, stop driving ... because a warped head is expensive" is the reason for
# that instruction, not for the thing asked about, so a cause that follows a conditional is left
# alone unless it is the answer's own first sentence.
CONDITIONAL = re.compile(r"\b(?:if|unless|once|when|before|after|until)\b", re.IGNORECASE)
# A sentence that opens with one of those words names a condition and what follows from it, so a
# clause cut out of it is the thing to do once the condition holds, not the cause asked for: "If
# one room still drops, a mesh wifi system (about £100 for two units) fixes it far better than a
# repeater" answers "what is going wrong" with a shopping list. The guard is on the sentence,
# because cutting the clauses first hands the consequence over on its own.
CONDITIONAL_SENTENCE = re.compile(
    r"^(?:if|unless|once|whenever|when|before|after|until|in case)\b", re.IGNORECASE)
INSTRUCTION = re.compile(
    r"\b(?:never|don'?t|do not|keep|call|ring|take|ask|check|make sure|you should|if you|try to|"
    r"avoid|be careful|watch|use|put|put it|store|leave it|cover it|fit|swap|replace)\b",
    re.IGNORECASE)
# A sentence splits into the explanation and the instruction at these, and the cause is on one
# side of them or the other: "...hitting cold surfaces, so ventilate" / "...with a dry cloth: the
# thin film stops the steam forming droplets".
PARTS = (": ", " - ", "; ")
# A reason hung on a bare `so` after the step it explains: "spit rather than rinse so the fluoride
# stays on". The determiner or pronoun after `so` is the test, because `so` in front of a verb is
# the next step (", so ventilate the room") and that is advice, not a reason.
SO_REASON = re.compile(
    r"\bso\s+(?:the|it|they|you|your|that|this|air|water|heat|warmth)\b",
    re.IGNORECASE)
# "since a 4-litre basket is one tray" is half a sentence: handed back as it stands it reads as a
# fragment ("Since a 4-litre basket is one tray."). The marker is put back by the frame instead,
# so the clause is handed over the same way "because" is ("Because a 4-litre basket is one tray").
LEADING_MARKER = re.compile(r"^(?:since|as|so)\s+(?=\w)", re.IGNORECASE)
# An answer that names its cause as a definition of the thing: "Most headaches are tension:
# muscles in the neck, jaw and scalp tighten with stress". The colon is the explanation of the
# claim in front of it, which is the reason asked for, but only where what follows reads as a
# clause and not as the instructions ("Here is what to do: soak the pot, let it dry through").
CLAIM_BEFORE_COLON = re.compile(r"^[^:]{4,}?\b(?:is|are|was|were)\b[^:]*:\s*(?P<why>[^:]{12,})$",
                               re.IGNORECASE)
CLAIM_SUBJECT = re.compile(r"^\s*(?:here|there|this|these|those|what|below|following)\b",
                           re.IGNORECASE)
IMPERATIVE = re.compile(
    r"^(?:soak|add|mix|stir|do|use|put|take|keep|leave|cover|store|check|try|avoid|don'?t|never|"
    r"give|wipe|wash|open|close|turn|set|ring|call|ask|make|let|get|go|run|start|stop|fill|"
    r"brush|floss|drink|eat|sit|stand|sleep|walk|stretch|reduce|cut|change|swap|replace|clean|"
    r"remove|apply|spread|heat|cook|boil|bake|roast|freeze|thaw|rest|massage|wear|hang|bin|"
    r"throw|unplug|label|write|book|hire|buy|sell|learn|practise|practice|repeat|look|watch|"
    r"listen|say|tell|note|remember|think|pick|choose|plan|sort|fit|trim|prune|water|feed|"
    r"move|top|blot|rinse|scrape|vacuum|spray|chop|slice|simmer|grill|season|serve|"
    # The verbs a step opens with that the list was missing, found by asking "why is that" after
    # the answer. "how long should i boil an egg" answers "Cool them in cold water for a minute
    # before peeling so the shell comes away cleanly", and the "so" made that clause a reason, so
    # the reply was "That's what is behind it: cool them in cold water for a minute" - a "why"
    # answered with the answer's last instruction. Every word here opens a step the same way the
    # kitchen and home words above do, so a clause that starts with one is a step and not a cause.
    r"cool|chill|drain|pat|press|squeeze|peel|whisk|steam|blanch|defrost|shake|dust|sweep|mop|"
    r"scour|polish|iron|sand|prime|seal|charge|reboot|restart|reset|update|empty|plug|tighten|"
    r"loosen|screw|glue|nail|drill|measure|mark|taste|knead|fold|roll|save|delete)\b",
    re.IGNORECASE)
# A part that says of itself that it is the fix is the thing to do, not the reason. "my sauce came
# out bitter" / "what am i doing wrong" was answered "Low heat, garlic in last and stirred for 30
# seconds is the fix next time - that's the reason", which labels a fix as a cause and is wrong on
# its face (spry-ring, #3685). The words are only the ones that name it as the fix: a sentence
# that says "the fix is a new washer" is still a fix and not a cause, while "the reason is the
# seal" is a cause and is left alone.
THE_FIX = re.compile(
    r"\b(?:is|was|are|'s) the (?:fix|answer|thing to do|way to do it)\b|\bfix next time\b|"
    r"\bthe fix (?:is|for|next time)\b|\bis how you (?:do|fix|stop|get)\b|"
    r"\bwhat (?:you do|to do) (?:next time|instead|now)\b",
    re.IGNORECASE)
# `CAUSE` lists the shapes the knowledge entries use, but English explains in more: "a wing is
# shaped so air moves faster", "cold makes tiny muscles pull your hairs upright, which traps a
# layer of air", "the blood vessels tighten, then widen again", "rain carries minerals to the
# sea and the water evaporates". These are reasons even though no `because` or `usually` is in
# them. A bare "why" that gets the honest shrug on top of one of these loses the turn it has
# already been given, so the opening sentence is read with this too.
# "the cause is damp, not the paint": an answer that names its cause outright, wherever it sits
# in the answer.
NAMED_CAUSE = re.compile(r"\b(?:the\s+)?(?:cause|reason)\s+(?:is|was)\s+(.+)", re.IGNORECASE)
EXPLAINS = re.compile(
    r"\b(?:because|since|so\s+(?:air|the|it|they|you)|"
    # "so warmth and time are the whole job": the reason as a clause with no cause word in it,
    # the shape a knowledge answer often writes it in. Without this the entry has the cause and
    # the reader declines anyway ("my sourdough is flat" / "what could be causing it").
    r"so\s+\w+(?:\s+\w+){0,4}\s+(?:are|is|was|were)\b|"
    r"when\b[^.!?]*\b(?:are|is|was|were)\b|"
    r"which\s+(?:makes|means|traps|tightens|widens)|"
    r"making\b|heats?\s+(?:\w+ )?(?:up\b|the\b|it\b|them\b|your\b|a\b)|"
    r"expands?|traps?|tightens?|wide(?:ns?|ned|ning)?|"
    r"carries|evaporat(?:es|ed|ing)|scatters?|tell(?:s|ing)?\b[^.!?]*\bto\b|"
    r"seems?\s+to)\b",
    re.IGNORECASE)
# A later sentence can carry a reason for the step before it, but it cannot stand alone as the
# answer: "If it is still there after that, see a GP..." points at a sentence we are not saying.
DANGLING = re.compile(
    r"^(?:(?:but|and|so|though)\s+)?(?:if\s+)?"
    r"(?:it|they|he|she|that|this|these|those)\b"
    r"|^(?:then|also|which|the same)\b",
    re.IGNORECASE)
# A figure after "so" is a result, not a cause: "20 minutes ... so a 2kg bird takes 1 hour 40".
RESULT_NUMBER = re.compile(r",\s*so\b[^.!?]*\d", re.IGNORECASE)
# A fault explained by its trigger: "a cake sinks when it's underbaked", "pastry cracks when it's
# too dry or too warm", "salmon dries out fast when it's overcooked". The trigger is the reason,
# and the words in front of it name what changes. Only a verb of change counts, so an answer that
# says when something is done ("it's done when a skewer comes out clean") or an instruction that
# names a moment ("replace them when the midsole feels flat") is not read as a cause.
CHANGE = re.compile(
    r"\b(?:sinks?|sank|rises?|rose|drops?|dropped|collapses?|collapsed|sags?|sagged|cracks?|"
    r"cracked|splits?|curdles?|curdled|separates?|separated|goes|went|gets|got|turns?|turned|"
    r"becomes?|became|sticks?|stuck|burns?|burnt|dries?|dried|toughens?|toughened|shrinks?|"
    r"shrank|smells?|smelt|tastes?|tasted|wrinkles?|wrinkled|tears?|tore|melts?|melted|sets?|"
    r"yellows?|yellowed|browns?|browned|wilts?|wilted|droops?|drooped|leaks?|leaked|clogs?|"
    r"clogged|overcooks?|overcooked|undercooks?|undercooked|overbakes?|overbaked|underbakes?|"
    r"underbaked|overmixes?|overmixed)\b",
    re.IGNORECASE)
WHEN_CAUSE = re.compile(r"\b(?:when|whenever)\b", re.IGNORECASE)
# Where the trigger ends and the advice begins: "custard goes lumpy when the heat is too high, so
# next time pour ..." carries the reason only up to the comma.
SO_FROM_HERE = re.compile(r",?\s+so\s+|;\s*", re.IGNORECASE)
# A reason handed back always carries a frame: the clause is often the answer's own sentence, and
# quoting it bare reads as the paragraph the person has just been given. "Since a 4-litre basket
# is one tray" as a whole reply was the fragment that made this necessary.
WHY_NAMED = (
    "That's what is behind it: {c}",
    "It comes down to this: {c}",
    "{c} - that's the reason.",
)
# The cause is quoted from the answer, so its own first letter is the answer's: "A cake sinks
# when ...", but also "a phone that is nearly full slows down badly". In a frame it is mid
# sentence, so the letter follows the frame ("That's what is behind it: a cake sinks when ...")
# and the opposite way round when the frame opens with the clause. A name and an acronym keep
# their capital, because "july" and "uV light" are not words.
KEEP_CAPITAL = frozenset((
    "i", "i'm", "i'd", "i've", "i'll", "monday", "tuesday", "wednesday", "thursday", "friday",
    "saturday", "sunday", "january", "february", "march", "april", "may", "june", "july",
    "august", "september", "october", "november", "december", "britain", "british", "england",
    "english", "london", "scotland", "wales", "ireland", "america", "american", "europe",
    "christmas", "easter", "god",
))


def _in_frame(frame, clause):
    """The clause put into a frame, with its first letter following the frame's sentence."""
    word = clause.split(" ", 1)[0].strip("\"'(*[")
    keep = word.lower().strip(".,!?:;") in KEEP_CAPITAL or word[1:2].isupper()
    if frame.startswith("{c}"):
        return frame.replace("{c}", clause)
    if keep or not clause:
        return frame.replace("{c}", clause)
    return frame.replace("{c}", clause[:1].lower() + clause[1:])
WHY_NAMED_BECAUSE = (
    "Because {c}",
    "That's because {c}",
    "{c} - that's the reason.",
)

# An answer that names its cause outright - "If it returns, the cause is damp, not the paint" -
# has already written the sentence this reply would be framing, so it is handed back as that
# sentence: "The cause is damp, not the paint." A frame on top of it read as a lead-in with a
# fragment after it (cobalt-ivy, #3685). It is a frame in the same way as the others, so
# `is_a_reason_line` can tell this line from an answer the bot wrote itself.
WHY_NAMED_SELF = (
    "The cause is {c}",
    "The reason is {c}",
)
# The front of every line this module says, so another composer can tell one of these from an
# answer it wrote itself. A reason handed back is spoken as the fallback module, like every other
# composer line, so a module name says nothing about it: the frame at the front is the only mark
# there is. It is derived from the pools above, because a pool that gains a frame and is not in
# here is a reason line the rest of the bot cannot see. The one frame that closes a line instead
# of opening it is kept on its own.
WHY_FRONT = frozenset(
    front for front in (frame.split("{")[0].strip().rstrip(":").strip().lower()
                        for frame in WHY_NAMED + WHY_NAMED_BECAUSE + WHY_NAMED_SELF)
                if front)
# The closing frame, with its full stop left off: the check below strips the end punctuation so a
# line that ends "that's the reason" and one that ends "that's the reason." are the same frame.
WHY_END = "- that's the reason"


def is_a_reason_line(text):
    """True when this is a cause this module handed back, not an answer of its own.

    "my phone battery drains fast" / "why is that" is answered "It's the reason I gave: social and
    video apps in the background are usually it", and the person then asks "is it dangerous". That
    question is about the phone, so whoever answers it has to read past this line to the answer the
    reason came out of: without this the verdict composer read the reason line as the answer and
    sent a worried person to a search engine instead of saying the boiler's bang is ordinary.
    """
    line = str(text or "").strip().lower().replace("\u2019", "'")
    if not line:
        return False
    if line.rstrip(" .").endswith(WHY_END):
        return True
    return any(line.startswith(front) for front in WHY_FRONT)

# The bot's last line was this module's own "I can't see the reason from here". A second "why" on
# top of that is the same question again, and the search hedge that main falls back to throws the
# thread away for a second time. The same honesty in a shorter form, and the one thing that would
# let the bot see it.
WHY_AGAIN = (
    "Because all I have is what you've told me, and the cause isn't in it - one more detail and I "
    "might see it.",
    "I still can't see the cause from here: it isn't in what you've told me. What does it do just "
    "before it goes wrong?",
    "The reason is still the part I can't reach from this side. When it goes wrong, what has just "
    "happened?",
)

WRONG_ANSWERED = (
    "I can't see what is going wrong from here, and I'd rather say so than invent a cause. Does "
    "it go wrong the same way every time?",
    "Nothing you've told me points at the cause, so I'd be guessing. Which part goes wrong - the "
    "start, the middle, or the end?",
    "I can't see what is wrong from here, and guessing would not help you. Talk me through what "
    "happens and I'll tell you what I can see in it.",
)

# A whole-answer ask about something that is not a process: no thirds to offer, just the honest
# "I would be inventing it" and one question that could let the bot see it.
WRONG_NOT_A_FAULT = (
    "I can't see a reason in what you've told me, and I'd rather say that than invent one. What "
    "happened just before it?",
    "Nothing you've told me points at a cause, and I won't guess at one. Talk me through what "
    "happened and I'll tell you what I can see in it.",
    "I don't know why, honestly. Tell me a bit more about how it came about and I'll say what I "
    "can see.",
)

WHY_NOT_ANSWERED = (
    "I can't speak for anyone else's reasons - only for what you can do about it. What was said "
    "when you raised it?",
    "Fair question, and I have no way of knowing what is behind it. What is their side of it?",
    "I can't tell why not from here. What is stopping it, as far as you can see?",
)

# "why not" about the bot's own advice: no third party, no invented motives. The reason is the
# one behind the suggestion - it is the version that works for most people - and the honest next
# thing is what would suit them instead.
WHY_NOT_ITS_OWN = (
    "No reason it has to be that way - it is the version that works for most people, not a rule. "
    "What is it about it that does not sit right?",
    "Only because it tends to be the one that works. If it does not suit you, say so and we will "
    "find another way.",
    "There is nothing wrong with the other way if it suits you. What are you weighing up?",
    "Mostly because it works for most people, not because it is the only way. What would you "
    "rather do?",
)


def _said_the_reason_cannot_be_seen(memory):
    """True when the bot's last line was this module's own answer to the same question.

    "why" asked twice in a row, or a "why" after "what could be causing it", is the same question
    unchanged, and a search hedge the second time reads as if the first answer had not happened.
    Only this module's own pools count, matched whole: a framed line carries the answer's own
    words, so it is not a shrug and a second "why" on it is not this case.
    """
    turns = memory.get("turns")
    if not isinstance(turns, list) or not turns or not isinstance(turns[-1], dict):
        return False
    said = str(turns[-1].get("bot") or "")
    return (said in WHY_ANSWERED or said in WHY_BODY or said in WRONG_ANSWERED
            or said in WHY_METHOD or said in WRONG_NOT_A_FAULT)


# "why do you think that", "why do you think so". Asked after an answer, this is the bare ask in
# more words: the bot's reasoning is "what makes you say that", and the self card answered a
# question about the bread with a paragraph about there being no mind behind it. Asked before
# anything has been said there is no answer to give a reason for, and the self card is right.
THINKS_BACK = re.compile(
    r"^\W*(?:(?:but|and|so|ok|okay|yeah|no|well|right)\s+)*"
    r"(?:why|y)\s+(?:do|did|would)\s+(?:you|u)\s+(?:think|thinking)\s+(?:that|so|this|it)"
    r"(?:\s+(?:then|though|tho))?[\s?!.,]*$",
    re.IGNORECASE)


def _is_bare_why(clean):
    """True when the whole line asks for the reason and nothing else."""
    return bool(BARE_WHY.match((clean or "").strip()))


def _last_turn(memory):
    """The turn above this one, or {} when there is nothing to explain.

    Turns memory keeps {"user", "bot", "module"} for each line. Only an answer that made a claim
    is worth asking the reason for: one of the ANSWERED modules, and long enough to be an answer.
    """
    turns = memory.get("turns")
    if not isinstance(turns, list) or not turns:
        return {}
    skipped_a_nod = False
    for last in reversed(turns[-3:]):
        if not isinstance(last, dict):
            return {}
        said = last.get("bot")
        if isinstance(said, str) and _answered_nothing(said):
            skipped_a_nod = True  # the bot's own nod: the answer being asked about is above it
            continue
        if last.get("module") in ANSWERED:
            if not isinstance(said, str) or len(said.split()) < SUBSTANCE:
                return {}
            if skipped_a_nod:
                reason = _reason_in(last)
                if not reason or THE_REASON_POINTS_AT_THE_ADVICE.match(reason):
                    # The nod is stepped over only where the answer under it can be explained from
                    # its own words. "how long does rice take" / "thanks" / "why" reads a timing
                    # answer, and the reason for it is the knowledge base's own why row ("Rice
                    # burns when there is no water left under it"): handing that turn to this
                    # module's shrug took five such chats from a real cause to "I don't know why".
                    #
                    # And a reason that opens on "that"/"this" is the answer's own advice saying
                    # why the advice works - "Cut saturated fat first, because that moves the
                    # number more than anything else". In the answer the antecedent is on the
                    # page; behind this module's "That's because ..." it is not, and the reply
                    # reads as nonsense that names nothing ("That's because that moves the number
                    # more than anything else"). So that answer is left to the module that wrote
                    # it, which hands its own sentence back with the antecedent still in it.
                    # Found by lavender-thimble and upbeat-badger reading this change.
                    return {}
            return last
        if last.get("module") == "greeting" and isinstance(said, str) and HEDGED.search(said):
            continue  # the bot's own shrug: the answer being asked about is above it
        return {}
    return {}


# The bot's own nod between the answer and the ask: "Alright then - good luck with it." after the
# boiler card, "Got it." after a fact. It answered nothing, so it is not the thing being asked
# about - yet it was read as the turn above, `_last_turn` found no claim in it and came back
# empty, and the `why` fell to the repeat frame: "my boiler is losing pressure" / "ok" / "why" got
# the whole card back as "Same as before: ..." where the same chat without the "ok" got "Because
# water is escaping somewhere." A nod is short, opens on a word of agreement or good wishes, and
# carries neither a step nor a cause; an answer with either in it is left alone.
A_NOD_OPENS = re.compile(
    r"^(?:alright|all\s+right|ok|okay|sure|got\s+it|noted|right|of\s+course|no\s+problem|"
    r"lovely|great|good|glad|happy|sorry|thanks|thank\s+you|fair\s+enough|makes\s+sense|"
    r"understood|will\s+do|cool|nice)\b", re.I)
A_NOD_IS_SHORT = 12
# A reason that points back at the answer's own advice instead of naming the thing: "Cut
# saturated fat first, because that moves the number more than anything else." The antecedent of
# "that" is the sentence in front of it, so the clause cannot stand on its own as the reply.
THE_REASON_POINTS_AT_THE_ADVICE = re.compile(r"^(?:because\s+|since\s+)?(?:that|this)\b", re.I)


def _answered_nothing(said):
    """True when a bot line is a nod rather than an answer: it gives no step and names no cause."""
    said = (said or "").strip()
    if not said or len(said.split()) > A_NOD_IS_SHORT:
        return False
    if IMPERATIVE.match(said) or INSTRUCTION.search(said) or CAUSE.search(said):
        return False
    if EXPLAINS.search(said) or NAMED_CAUSE.search(said):
        return False
    return bool(A_NOD_OPENS.match(said))


FIRST_SENTENCES = 2


# The answer above was the how-to and nothing else, so the reason is not in it - but neither is
# the bot empty-handed, and "I can't see what is wrong from here" is the same sentence for a loaf
# of bread and a tray of potatoes (spry-ring, #3685). The reply says which half it can stand
# behind, so the person knows the steps are not being withdrawn and what to tell the bot next.
WHY_METHOD = (
    "Those steps are the how-to; the reason under them is the part I'd be guessing at. Tell me "
    "what happens and I'll say what I can see.",
    "Everything I gave you there is what to do, not why it happens - that half isn't in what I "
    "have. What is it doing when it goes wrong?",
    "The method is what I can stand behind. The cause is the bit I can't see from here, so tell me "
    "what it does and I'll work it back from that.",
)


def _gave_a_method(last):
    """True when the answer above was the how-to and said nothing about why it goes wrong."""
    said = str(last.get("bot") or "")
    if not said:
        return False
    if CAUSE.search(said) or EXPLAINS.search(said) or NAMED_CAUSE.search(said):
        return False
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", said) if s.strip()]
    steps = [s for s in sentences if IMPERATIVE.match(s) or INSTRUCTION.search(s)]
    return bool(steps) and len(steps) * 2 >= len(sentences)


def _a_cause_named_outright(last):
    """The cause the answer above names as a cause, or "" when it only has a "because" clause.

    For "why not", where the answer's positive reason said back as a reason not to is the
    opposite of what it wrote. The two shapes that name a cause on their face are the thing in
    front of a colon ("It is the caffeine: it peaks about half an hour after the cup ...") and
    "the cause is ...".
    """
    said = str(last.get("bot") or "")
    for sentence in re.split(r"(?<=[.!?])\s+", said)[:FIRST_SENTENCES]:
        text = sentence.strip()
        if IMPERATIVE.match(text):
            continue
        named = NAMED_CAUSE.search(text)
        if named and not THE_FIX.search(text):
            cause = named.group(1).strip().rstrip(".,;:")
            if len(cause.split()) >= 2:
                return cause
        thing = A_THING_NAMED_BEFORE_A_COLON.match(text)
        if thing:
            return "the " + thing.group("thing").strip()
    return ""


def _reason_in(last, strict=False):
    """The cause the answer above already named, as one clause, or "" when it named none.

    An answer sometimes carries an example in its own quotation marks, and the "because" in it is
    the example's reason, not the answer's: "A thesis statement is one sentence that says the
    claim your essay will prove, and why it matters: `Cheaper public transport would cut city
    emissions more than electric cars, because most journeys are short.` Put it at the end of your
    first paragraph" answered "and why does it matter" with "Because most journeys are short." Put
    it at the end of your first paragraph - the reason out of somebody else's sample sentence, cut
    where its own sentence ended. So a reason found inside a quotation is thrown away and the
    answer is read again without its examples. What is left is the answer's own claim, and if it
    names no reason the shrug is the honest reply.
    """
    said = str(last.get("bot") or "")
    reason = _a_reason_in(said, strict=strict)
    if reason and _inside_a_quotation(said, reason):
        return _a_reason_in(_without_examples(said), strict=strict)
    return reason


# A quotation an answer sets out as an example: straight or curly double quotes, at least a few
# words long, so a pair of marks around one word is not read as an example.
EXAMPLE_IN_QUOTES = re.compile('"[^"]{4,}"|\u201c[^\u201d]{4,}\u201d')


def _without_examples(said):
    """The answer with its quoted examples taken out, so their words cannot be handed back."""
    return EXAMPLE_IN_QUOTES.sub(" ", str(said or ""))


def _inside_a_quotation(said, clause):
    """True when the clause sits inside a quotation in the answer, so it is an example's words."""
    said = str(said or "")
    at = said.find(clause)
    if at <= 0:
        return False
    before = said[:at]
    marks = before.count('"') + before.count("\u201c") + before.count("\u201d")
    return marks % 2 == 1


def _a_reason_in(said, strict=False):
    """The cause the answer above already named, as one clause, or "" when it named none.

    Quoting the bot's own answer invents nothing: the words were said on the turn before. It is
    cut to the clause that carries the cause, because the rest of the answer is the advice the
    person already has.

    The sentences are read twice. The first reading only takes a part that is not an instruction,
    because a part that starts with one is what to do, not why it happened: "take it off the heat,
    because the smoky taste spreads" and "wipe the mould off, then stop it coming back" carry
    cause words and would answer "why" with a to-do list. Only when the answer names its cause
    nowhere else does the second reading take those parts too, which is what it did before the
    line shapes here were widened - so a line that used to get a reason still gets one.
    """
    whole = re.split(r"(?<=[.!?])\s+", said)
    sentences = whole[:FIRST_SENTENCES]
    # The cause can be named in front of the colon with its mechanism behind it ("It is the
    # caffeine: it peaks about half an hour after the cup ..."). Read before the other passes,
    # because the mechanism usually carries a figure ("half an hour") and a timing rule is
    # skipped further down as a result rather than a reason.
    for sentence in sentences:
        text = sentence.strip()
        if IMPERATIVE.match(text):
            continue
        named = (A_THING_NAMED_BEFORE_A_COLON.match(text)
                 or A_THING_NAMED_BEFORE_A_COLON.match(A_LEAD_IN.sub("", text)))
        if named:
            return "the " + named.group("thing").strip()
        short = SHORT_OF_A_CAUSE.match(text)
        if short:
            cause = " ".join(short.group("cause").split()).rstrip(".,;:")
            if len(cause.split()) >= 2:
                return cause
    # "what am i doing wrong" is asking what is wrong with the thing, so a reason that is the
    # reason for one of the instructions ("take it off the heat, because the smoky taste spreads")
    # is not an answer to it. The bare "why" keeps the second reading it has always had.
    # An answer sometimes names its cause outright, and usually at the end, after the steps:
    # "wipe the mould off ... If it returns, the cause is damp, not the paint." That sentence is
    # the reason whatever else it starts with, and it is read before the passes below so the
    # "If ..." guard and the instruction guard cannot skip it. Only a sentence that names the
    # cause is taken this way, so a closing "see a GP if it spreads" cannot come back as one.
    for sentence in whole:
        found = NAMED_CAUSE.search(sentence)
        if (not found or INSTRUCTION.search(sentence) or RESULT_NUMBER.search(sentence)
                or THE_FIX.search(sentence)):
            continue
        clause = found.group(1).strip().rstrip(".,;:")
        if len(clause.split()) >= 2:
            return clause
    # "Warmth, damp and the plastic bag it came in are what mould needs, so a loaf in a warm
    # kitchen goes green within days" names its cause in front of the consequence: the thing the
    # mould needs is the why, and the green loaf is what follows. Without this the sentence was
    # read as naming no cause at all, and a "why do you think so" after it got the whole answer
    # back with "Same as before" in front - the repeat STYLE.md ranks lowest, for an answer that
    # had a reason in it. Only the half in front of the consequence comes back, because the rest
    # is what the person already read.
    for sentence in sentences:
        named = WHAT_IT_TAKES.search(sentence)
        if named and not IMPERATIVE.match(sentence.strip()):
            clause = named.group(1).strip().rstrip(".,;:")
            if len(clause.split()) >= 3:
                return clause
    passes = (False,) if strict else (False, True)
    for instruction_ok in passes:
        for number, sentence in enumerate(sentences):
            if RESULT_NUMBER.search(sentence):
                continue  # a timing rule is a result, not a reason
            if number and DANGLING.match(sentence.strip()):
                continue  # "If it is still there after that..." needs the sentence before it
            if number and not instruction_ok and INSTRUCTION.search(sentence):
                continue  # the reason for that step, not for the answer as a whole
            if CONDITIONAL_SENTENCE.match(sentence.strip()):
                # "If one room still drops, a mesh wifi system (about £100 for two units) fixes it
                # far better than a repeater" is a remedy someone may act on, not a cause: the
                # sentence is conditional and the clause cut from it is a shopping list.
                continue  # when and then, not why
            trigger = _trigger_in(sentence)
            if (trigger and not THE_FIX.search(trigger)
                    and not (number and INSTRUCTION.search(sentence))):
                # The trigger shape is cut where the advice starts, so it is preferred to the
                # whole sentence for the same reason: "Custard goes lumpy when the heat is too
                # high or the eggs go in too fast" is the reason, and "so next time pour the hot
                # milk in ..." is the plan the person already has.
                return trigger
            if (not CAUSE.search(sentence) and not CLAIM_BEFORE_COLON.match(sentence.strip())
                    and EXPLAINS.search(sentence) and not IMPERATIVE.match(sentence)
                    and not THE_FIX.search(sentence)
                    and not CONDITIONAL_SENTENCE.match(sentence.strip())
                    and not DOSE.search(sentence)
                    and not _is_the_answer_itself(said, sentence)):
                # One sentence is not the paragraph: hand the explanation back whole rather than
                # chopping it at the last comma, which dropped the `making a shock wave` and
                # `which traps a layer of air` halves that carry the reason.
                clause = sentence.strip().rstrip(".,;:")
                if len(clause.split()) >= 3:
                    return clause
            # The explanation and the instruction are usually on opposite sides of a colon or
            # dash, so each part is tried on its own before the whole sentence is given up on.
            if CONDITIONAL_SENTENCE.match(sentence.strip()):
                continue  # when and then, not why
            parts = [sentence]
            for mark in PARTS:
                parts = [piece for part in parts for piece in part.split(mark)]
            for part in parts:
                clause = _cause_clause(part, number, instruction_ok)
                if clause and not THE_FIX.search(clause):
                    if strict and _carries_the_fix(sentence, clause):
                        # "Gluey starch is nearly always too much water and too much stirring:
                        # stop stirring it, drain it" - the sentence names the cause and then,
                        # after the colon, what to do about it. "What am i doing wrong" wants
                        # both halves, and cutting at the colon dropped the useful one.
                        return sentence.strip().rstrip(".,;:")
                    return clause
                trigger = _trigger_in(part)
                if (trigger and not THE_FIX.search(trigger)
                        and not (number and INSTRUCTION.search(part))):
                    return trigger
    named_class = _named_by_definition(said)
    if named_class:
        return named_class
    # The class the answer put the thing in ("Most back pain is muscular") is its cause as plainly
    # as a `because` clause is, and it is the one shape with no cause word in it at all. Read last,
    # so a colon that names the cause in a list ("most constant tiredness is dull rather than
    # medical: too little sleep, a late screen") still hands that list back rather than the class,
    # and only an answer whose colon holds instructions ("...what helps most: keep walking") is
    # left for the class.
    return _the_class_it_belongs_to(said)


# The cause said as what the thing needs, in front of the consequence: "X and Y are what mould
# needs, so ...". The first half is the reason; the second is the result the person already has.
WHAT_IT_TAKES = re.compile(
    r"^(?P<thing>[^.;:]{4,}?\b(?:is|are)\s+what\b[^,.;]{0,40}?(?:needs?|wants?|feeds?|"
    r"thrives? on|likes?|goes? for)\b[^,.;]*)[,.;]?\s+so\b", re.I)


# The cause can also be named before a colon with its mechanism behind it: "It is the caffeine:
# it peaks about half an hour after the cup and takes five or six hours to leave your system".
# `_named_by_definition` reads what follows a colon, which here is the mechanism rather than the
# thing itself, so the answer named its cause and still declined ("why not" after the coffee
# entry got "I can't tell why not from here"). What the person is owed is the thing named.
A_THING_NAMED_BEFORE_A_COLON = re.compile(
    r"\A(?:it|that|this)\s+(?:is|was|isn'?t|wasn'?t)\s+"
    r"(?:almost\s+always\s+|nearly\s+always\s+|usually\s+|often\s+|just\s+)?"
    r"(?:the|a|an|your|too\s+much|not\s+enough|too\s+little)\s+(?P<thing>[a-z][^:,.;!?]{1,40}?)"
    # The cause is often named with what it is not: "it is the roots, not the light".
    r"(?:,\s*(?:not|rather\s+than)\s+(?:the\s+|a\s+|your\s+)?[a-z][^:,.;!?]{1,25})?"
    r"\s*:\s*\S",
    re.IGNORECASE)

# A frequency phrase in front of the cause is still the cause, and it is how most of the knowledge
# cards open one: "Nine times in ten it is the roots, not the light: check the compost an inch down
# and the drainage holes". Read only from the start of the sentence, the colon reading above needs
# the line to open on "it is", so it missed it and the answer that named its cause twice was told
# "I can't see what is wrong from here" (whyfollow-07).
A_LEAD_IN = re.compile(
    r"\A(?:(?:nine|eight|seven|six|five|four|three|two)\s+times\s+(?:in|out\s+of)\s+"
    r"(?:ten|twenty|a\s+hundred|\d+)|most\s+of\s+the\s+time|more\s+often\s+than\s+not"
    r"|usually|nearly\s+always|almost\s+always|in\s+my\s+experience|as\s+a\s+rule"
    r"|nine\s+times\s+out\s+of\s+ten)\s+",
    re.IGNORECASE)

# The cause said as what the thing is short of, which is how a baking or a keeping entry writes it:
# "A bake that stays pale is short of heat or short of sugar". The sentence is a cause from end to
# end, so what comes back is the shortage and not the whole line.
SHORT_OF_A_CAUSE = re.compile(
    # A pronoun in front is not a thing being short of something: "it is not enough to say sorry"
    # is a judgement about what is enough, not the cause of anything.
    r"\A(?!(?:it|that|this|there|which)\b)[^.;:]{3,60}?\s+(?:is|are|was|were)\s+"
    r"(?:usually\s+|nearly\s+always\s+|almost\s+always\s+|often\s+|probably\s+|just\s+)?"
    r"(?P<cause>(?:short\s+of|low\s+on|lacking|too\s+much|too\s+little|not\s+enough)\b"
    r"[^.;:]{1,60})",
    re.IGNORECASE)
AFTER_THE_MARK = re.compile(r"^\s*(?::| - |; )\s*(?P<rest>.+)$")


def _is_the_answer_itself(said, sentence):
    """True when this sentence is the whole answer, so handing it back explains nothing.

    A one-sentence answer has no paragraph for the sentence to be a part of. Handing it back to
    "why" gives the person the line they have just read with a frame in front of it: "That's what
    is behind it: Six to eight glasses a day, about 1.5 to 2 litres, is plenty, and more in heat
    or after exercise..." is not one word of reason, and the advice in it reads as if it were the
    reason. The reading goes on to the parts below, where a `so` clause inside the sentence can
    still name the cause ("spit rather than rinse so the fluoride stays on"); when there is none
    the honest shrug is the reply, which is more use than the answer again.

    Only a sentence that carries nearly every word of the answer counts. A sentence of a longer
    answer is a part of it, and one that is most of a two-sentence answer is still not the whole
    thing.
    """
    whole = _words(said)
    part = _words(sentence)
    if not whole or not part:
        return False
    return len(part) >= max(3, int(len(whole) * 0.9))


def _words(text):
    """The words of a line, folded, so punctuation and case cannot hide a repeat."""
    return [word for word in re.split(r"[^a-z0-9']+", str(text or "").lower()) if word]


def _carries_the_fix(sentence, clause):
    """True when the sentence says the cause and then the fix after its colon or dash."""
    rest = sentence.strip()
    if not rest.startswith(clause):
        return False
    found = AFTER_THE_MARK.match(rest[len(clause):])
    return bool(found and IMPERATIVE.match(found.group("rest").strip()))


def _trigger_in(part):
    """The reason when the answer explains a fault by its trigger, else "".

    "A cake sinks when it's underbaked", "pastry cracks when it's too dry or too warm": the
    change comes first and the condition that makes it happen comes after `when`, so the whole
    clause, cut where the advice starts, is the reason. It invents nothing - the words were said
    on the turn before - and it is the shape most keeping and cooking entries use to explain a
    fault. An instruction ("replace them when the midsole feels flat") and a definition ("it's
    done when a skewer comes out clean") are not causes, so they keep the honest shrug.
    """
    text = str(part or "").strip()
    if not text or IMPERATIVE.match(text) or CONDITIONAL.match(text) or NEGATIVE.search(text):
        return ""
    for match in WHEN_CAUSE.finditer(text):
        head = text[:match.start()].strip()
        if len(head.split()) < 2 or not CHANGE.search(head):
            continue
        clause = SO_FROM_HERE.split(text[match.start():])[0]
        # "Pastry cracks when it's too dry or too warm: sprinkle on a little cold water" - the
        # colon is where the reason stops and the fix starts, the same split the rest of the
        # module uses.
        clause = clause.split(": ")[0]
        clause = (head + " " + clause).strip().rstrip(".,;:").strip()
        clause = _cut_long(clause)
        if len(clause.split()) < 4:
            continue
        return clause
    return ""



def _cause_clause(part, number, instruction_ok):
    """The cause in one part of a sentence, as a clause, or "" when it names none."""
    found = CAUSE.search(part)
    # "spit rather than rinse so the fluoride stays on" carries its reason on a bare `so`: the
    # instruction is the step, and what follows `so` is why the step is worth doing. `CAUSE` does
    # not take a bare `so` because most of them introduce advice (", so open a window"), so the
    # pronoun after it is what tells the two apart - "so the fluoride stays on" names a thing and
    # what it does, ", so ventilate" names a step.
    if not found:
        found = SO_REASON.search(part)
    if not found:
        return ""
    if number and INSTRUCTION.search(part):
        return ""
    if not instruction_ok and IMPERATIVE.match(part.strip()):
        return ""
    if found.group(0).lower() in ("because", "since"):
        prefix = part[:part.lower().find(found.group(0).lower())]
        if NEGATIVE.search(prefix) or CONDITIONAL.search(prefix):
            return ""
    # "because"/"since" start the cause themselves, and so does a bare `so` in front of its own
    # subject ("so the fluoride stays on"); the other markers need the subject in front of them,
    # or the line comes out as "stops the smell coming back".
    from_the_marker = (found.group(0).lower() in ("because", "since")
                       or found.re is SO_REASON)
    clause = (part[part.lower().find(found.group(0).lower()):]
              if from_the_marker else part)
    clause = SO_ADVICE.split(clause)[0]
    clause = AND_STEP.split(clause)[0]
    clause = AND_ADVICE.split(clause)[0]
    clause = LEADING_MARKER.sub("because ", clause.strip(), count=1)
    clause = clause.strip().rstrip(".,;:").strip()
    clause = _cut_long(clause)
    if len(clause.split()) < 3:
        return ""
    # "wipe the mould off, then stop it coming back" is a to-do list, whatever cause word is in
    # it. Only a clause that starts with the reason itself is handed back as one.
    if not clause.lower().startswith(("because ", "since ")) and IMPERATIVE.match(clause):
        return ""
    return clause


# A generalization about the thing is a cause, and it is how the health and home entries write the
# reason most often: "Most back pain is muscular and settles in two to six weeks", "Most shoulder
# pain is a strained or trapped tendon", "Most bad breath is bacteria on the tongue and between the
# teeth, not the stomach", "Most rashes are contact or heat". No cause word marks any of them, so the
# clause sets were read and the answer was told it named no cause at all - "my back aches in the
# mornings" / "why is that" got "I don't know the reason, and I'd rather say so than invent one"
# directly under the bot's own "Most back pain is muscular". A bot that disowns the line above it is
# worse than one that repeats it, so the class the answer named is handed back as the reason.
#
# The claim is only the reason when it says what the thing IS. "Most back pain is muscular" is the
# why; "Most cars want an oil and filter change every 12 months" is a schedule, "Most sharks live 20
# to 30 years" is a lifespan, and both answer "how often" rather than "why". So the complement is
# cut at the first clause boundary and kept only when what is left is a noun or adjective class:
# no figure in it, and none of the verbs the entries use to say what a thing does.
A_GENERAL_CLAIM = re.compile(
    r"\A(?:most|almost\s+all|nearly\s+all|in\s+most\s+cases|the\s+majority\s+of|mostly)\s+"
    r"(?P<subject>[^.;:,]{2,60}?)\s+(?:is|are|was|were)\s+(?P<what>[^.;:]{2,140})",
    re.IGNORECASE)
# Where the class ends: the claim in front of these is the thing itself, and behind them is what to
# do about it or how long it lasts ("muscular and settles in two to six weeks", "contact or heat: a
# new soap or washing powder").
ENDS_THE_CLASS = re.compile(r"(?::|,| - | and | so | which | but | worse )", re.IGNORECASE)
# The complement says what the thing does, so a "why" answered by it is the answer again: "Most
# fevers from a virus settle within two or three days", "Most couples take" the complement away
# from the cause. These are the doing verbs the entries actually use in a `Most ... is ...` line.
SAYS_WHAT_IT_DOES = re.compile(
    r"\b(?:want|wants|need|needs|live|lives|take|takes|last|lasts|go|goes|come|comes|get|gets|"
    r"settle|settles|heal|heals|die|dies|cost|costs|help|helps|work|works|hold|holds|keep|keeps|"
    r"put|puts|eat|eats|do|does|say|says|give|gives|pay|pays|rise|rises|fall|falls|start|starts|"
    r"finish|finishes|run|runs|turn|turns|sit|sits|charge|charges|cover|covers|include|includes|"
    r"pass|passes|count|counts|matter|matters|mean|means|stay|stays|carry|carries)\b",
    re.IGNORECASE)
# A complement that is only a place-holder says nothing about why: "Most of it is air", "Most are
# harmless". The class has to name a thing the person can act on.
A_PLACEHOLDER = frozenset(("it", "this", "that", "them", "they", "one", "so", "true", "fine",
                           "ok", "okay", "normal", "harmless", "nothing", "none", "air", "you",
                           "me", "us"))


def _the_class_it_belongs_to(said):
    """The class the answer said the thing belongs to, as the reason for it, or "".

    Read from the answer's own opening sentence, because that is where an entry puts what the thing
    is: "Most back pain is muscular and settles in two to six weeks, and staying active is what
    helps most". What comes back is the claim as it stands, not a rewrite of it, so the reply is the
    bot's own words: quoting them invents nothing.
    """
    first = re.split(r"(?<=[.!?])\s+", str(said or "").strip())[0].strip()
    if IMPERATIVE.match(first) or CONDITIONAL_SENTENCE.match(first):
        return ""
    found = A_GENERAL_CLAIM.match(first)
    if not found:
        return ""
    claim = ENDS_THE_CLASS.split(found.group("what"), 1)[0].strip().rstrip(".,;:")
    # The class is what the thing is, so it is a short noun or adjective phrase: a doing verb, a
    # figure or a place-holder means the answer was saying how often or how long, not why.
    if len(claim.split()) < 1 or len(claim.split()) > 14:
        return ""
    if SAYS_WHAT_IT_DOES.search(claim) or re.search(r"\d", claim):
        return ""
    if claim.lower() in A_PLACEHOLDER or THE_FIX.search(claim):
        return ""
    if INSTRUCTION.search(claim) or DOSE.search(claim):
        return ""
    subject = found.group("subject").strip()
    lead = first[:found.start("what")].strip()
    return "{} {}".format(lead or "Most " + subject, claim)


def _named_by_definition(said):
    """The reason when the answer gives it as a definition: "Most headaches are tension: ...".

    Some answers say what the thing is and then say what that means, and the part after the colon
    is the reason the person is asking for. It is only taken when the claim in front of the colon
    is about the thing and not an announcement ("here is what to do"), and when what follows reads
    as a clause rather than as instructions, so the reason handed back is never an order.
    """
    for sentence in re.split(r"(?<=[.!?])\s+", str(said or ""))[:1]:
        found = CLAIM_BEFORE_COLON.match(sentence.strip())
        # A sentence that opens with a verb is a step, and the colon in it splits the step from
        # the next one: "Check the disk is not full, then cut what starts with the machine: Task
        # Manager > Startup, and turn off the things you do not need" has an `is` in front of its
        # colon and nothing that explains anything behind it. Only a claim about the thing can
        # carry its reason after a colon.
        if not found or CLAIM_SUBJECT.match(sentence) or IMPERATIVE.match(sentence.strip()):
            continue
        why = found.group("why").strip().rstrip(".,;:")
        # What comes after the colon is the reason only when it says what the thing is. A quoted
        # line ("Say the one thing under the argument: 'When we get together...'") is what to say,
        # not why it happens.
        if why[:1] in "\"'\u2018\u201c" or IMPERATIVE.match(why) or INSTRUCTION.match(why):
            continue
        why = SO_ADVICE.split(why)[0].strip().rstrip(".,;:")
        why = _cut_long(why)
        if len(why.split()) < 4:
            continue
        return "because " + why[0].lower() + why[1:]
    return ""


def _cut_long(clause):
    """The clause at its own comma, or "" when it only ends where the character limit is.

    `"...and if that fails make..."` is a cut-off instruction handed back as a reason. A clause
    that has to be chopped is not a reason this module can stand behind.
    """
    words = clause.split()
    if len(words) <= 24:
        return clause
    head = " ".join(words[:24])
    at = max(head.rfind(", "), head.rfind(" - "))
    if at < len(head) // 3:
        return ""
    return head[:at]


# An answer shorter than this is a sentence the person can reread as it stands, so handing it
# back is not handing a paragraph back - and on those lines the knowledge module's own narrowing
# (the newest sentence it has) is the better reply, so the composer leaves them alone.
ANSWER_LONG = 18


# An answer that tells the person to act now is answered by the answer itself, so a why about it
# gets the card again rather than the reason cut out of it: "Pull over, switch the engine off" is
# the reply to "what is causing it" when the engine is overheating, and the "same-day call" tail
# belongs with "what could be causing it" after the numb hands (rose-heather, gray-cypress).
# Only a warning about harm counts. "See a physio if it swells" is the tail of half the health
# answers and those still give up their reason, which is what the person asked for.
ACT_NOW = re.compile(
    r"\b(?:999|911|112|a&e|a and e|ambulance|paramedic|unconscious|"
    r"not breathing|can'?t breathe|scald\w*|never open|still hot|poison\w*|gas leak|on fire|"
    r"stop driving|pull over|don'?t wait|do not wait|stay on the line)\b",
    re.IGNORECASE)
# "The same day", "straight away", "today", "111": the GP-this-week phrasing, which is in 87 of the
# knowledge answers as the tail of ordinary advice ("get advice the same day if you cannot keep any
# drink down"). Standing aside for it handed back the whole paragraph with "Same as before" in
# front - the one repeat this module exists to stop (hardy-pen, #3685). It is a warning only where
# the sentence does not hang it on a condition: "Numbness on one whole side is a same-day call" is
# the alarm of the numb-hands card, and the person is owed that sentence (rose-heather,
# gray-cypress).
ACT_NOW_SOON = re.compile(
    r"\b(?:111|same[- ]day|straight away|right away|immediately|today)\b",
    re.IGNORECASE)
# A caution is not a warning: "see a GP if it wakes you most nights" is the tail of half the
# answers, and so is "the same day if ...". The conditional is what makes it wait for something.
CONDITIONAL = re.compile(r"\b(?:if|unless|should|in case|any time)\b", re.IGNORECASE)
SENTENCE = re.compile(r"[^.?!;]+[.?!;]?")


def _an_answer_to_act_on(last):
    """True when the answer above says to act now, so the reason is not read out of it."""
    said = str(last.get("bot") or "")
    if not said:
        return False
    if ACT_NOW.search(said):
        return True
    for sentence in SENTENCE.findall(said):
        if ACT_NOW_SOON.search(sentence) and not CONDITIONAL.search(sentence):
            return True
    return False


# A line that says the answer above was not followed, without saying which bit: "what?", "sorry,
# what", "come again", "say that again", "what do you mean", "i dont get it". Every one of them
# was answered by handing the text above back - "Same as before: <the paragraph>", "I said: <the
# paragraph>", "Sure - <the paragraph>", "It's what I said a moment ago: <the paragraph>" - and
# the paragraph handed back is the one they just said they did not follow. Repeating it at the
# same length cannot help; saying the same thing in fewer words can.
SAID_AGAIN = re.compile(
    # "so what" is the dismissive one, not the repeat, and it reads as the prefix "so" plus "what".
    r"^(?!so\s+what\b)"
    r"(?:(?:sorry|ok|okay|er|erm|um|eh|and|so|but|wait|no|yes)[\s,]+)*"
    r"(?:"
    # The word on its own, half a dozen spellings of it, and the repeated question mark people
    # type when they have not followed a word of it.
    r"what|wat|wot|wut|huh|pardon"
    r"|what\s+did\s+(?:you|u)\s+say"
    r"|what\s+(?:was|is)\s+that"
    r"|say\s+(?:that|it)\s+again|say\s+again|come\s+again|run\s+that\s+by\s+me\s+again"
    # Not "you what": that is disbelief, not a repeat - the composer reads it as one in
    # `bot/compose/reaction.py` and answers it from the doubt pool, so a claim here would put this
    # module's shorter answer behind the doubt pool's wording (found on `can i defrost mince in the
    # microwave` / `you what`).
    r")"
    r"(?:\s+(?:sorry|please|mate|then|now))?[\s?!.,]*$",
    re.IGNORECASE)
# "What do you mean" and "I don't follow" are the same noise on the surface and a different ask
# underneath: they ask what the bot was getting at, and the memory store answers those by handing
# over the sentence it meant, which is the right reply. Only the lines above - the words did not
# arrive at all - are this module's, because all they can be given is the same thing said shorter.
# The same answer in fewer words, which is the one thing a person who did not follow it can use.
# The frame is the module's own, so the shortened sentence carries it and the person is not told
# the bot is repeating itself: that is what they already knew when they typed "what?".
AGAIN_SHORTER = (
    "In short: {short}",
    "Shorter: {short}",
    "The short of it: {short}",
    "The gist of it: {short}",
)
# The lead-ins those short forms carry, so an answer that is already one is not read as a fresh
# paragraph and shortened a second time ("The gist of it: From just now: ...").
REPEAT_LEADS = tuple(str(frame).split("{short}")[0] for frame in AGAIN_SHORTER)
# Where a long sentence can be cut to make a shorter one: at a colon or a semicolon, which is where
# an answer stops saying the thing and starts explaining it or adding to it. Not a dash and not a
# comma: "Fill a freezer bag with white vinegar - half vinegar, half water if the chrome worries
# you - tie it over the shower head..." cut at the first dash is a third of an instruction.
CLAUSE_END = re.compile(r":\s+|;\s+")
# A clause shorter than this is a label, not the thing ("The things that work."), so the cut moves
# on to the next one and the answer is left for the question when there is none.
# How much shorter the answer has to be before "In short:" is honest: a frame in front of the
# same words is a label, not a short form of anything.
_A_SAVE_LEAST = 5
_A_CLAUSE_LEAST = 6
# A sentence longer than this is read for its own first clause before it is handed back whole: at
# this length the sentence is two thoughts, and the frame in front of it claims a short form it is
# not. Below it the sentence is one thought with an aside in it, and the aside is usually the part
# that explains the thought.
_A_LONG_SENTENCE = 25
# And the clause is only taken when it is at most this fraction of the sentence it opens. A clause
# that is half of a long sentence is half of one thought, and the half left behind is usually the
# part to act on: "A machine that bangs or walks across the floor is almost always an uneven load:
# stop it, undo the tangle..." cut at its colon names the cause and drops the fix. A clause that
# opens a long list is a stride before it: "Defrost it when the ice is more than about 5mm thick:"
# is the whole instruction and the list after it is the detail.
_A_STRIDE = 3
# A shortening that runs past this many words is not one: the answer's own opening sentence is
# dropped for the question instead, because a shortened answer that still needs shortening has
# not been made any easier to follow.
AGAIN_WORDS = 40
# The answers whose opening sentence is not the part to keep. A health answer opens on the harmless
# half ("a lump that comes up over a few days is usually a swollen gland") and closes on the bit to
# act on ("get it checked if it is still there in three weeks"): handing back the opening says the
# reassuring half and drops the sentence that matters, on the one kind of answer where that is not
# a loss of detail but a loss of the point. `ACT_NOW` above already keeps the cards that say 999 or
# same-day; this is the ordinary "see a GP if" answer, and no cut of it is handed back at all: the
# module that wrote it says it again whole. A shortened health answer is not a risk worth taking
# for the sake of a shorter one, and the pointer question is worse than both - it hands the person
# nothing when the answer's own words would have (`i havent slept properly in weeks / what?` got
# "That was all one go - say which part lost you" where main's own hand-back was the reassurance).
NO_CUT = re.compile(
    # The route out of the answer, anywhere in it: "needs a GP", "see your doctor", "ring 111".
    r"\b(?:gp|doctor|nurse|pharmacist|chemist|dentist|physio\w*|midwife|health visitor|"
    r"111|999|a&e|hospital|ambulance|paramedic)\b"
    # Or the thing to go and have done, said without naming who does it.
    r"|\b(?:get|have)\s+it\s+(?:checked|looked at|seen)\b"
    r"|\bworth\s+(?:getting|having)\s+.{0,30}?(?:checked|looked at)\b", re.IGNORECASE)
# Where a sentence ends, for a short form made of the answer's own first sentence. The split is on
# a full stop or a question mark with a space after it, so the point in "1.5 bar" and the "e.g." in
# the middle of a sentence are not ends - reading one as an end cut "between 1 and 1.5 bar" down to
# "between 1 and 1" (the boiler answer).
END_OF_SENTENCE = re.compile(r"(?<=[.!?])\s+")


# An answer that opens by taking the news in ("Sorry - that is a rough one.") and then does the
# practical thing. Shortening it to that first sentence keeps the sympathy and drops the help, and
# the frame makes it worse: "In short: Sorry - that is a rough one." is a form letter. The stock
# repeat line asks which bit instead, and the answer is still there for them to point at.
OPENS_ON_CARE = re.compile(
    r"^(?:ok|okay|right|well|oh|ah|aw|ugh|sorry)?[\s,\u2014-]*"
    r"(?:i'?m (?:really |so )?sorry|sorry|that (?:is|was) (?:a rough|rough|tough|hard|a lot)|"
    r"no wonder|that sounds|lousy|horrible|awful|poor you|rough one)\b", re.IGNORECASE)


def _first_sentence(said):
    """The answer's own opening sentence, or "" when it has only one."""
    said = " ".join(str(said or "").split())
    if not said:
        return ""
    parts = [part.strip() for part in END_OF_SENTENCE.split(said) if part.strip()]
    if len(parts) < 2:
        return ""
    return parts[0].rstrip(",;:- ")


def _a_shorter_way(said):
    """The answer above said shorter, or "" when there is nothing in it to cut down to.

    In order: the answer's opening sentence, cut at a colon or semicolon when that sentence is a
    long one and the cut is a real clause; the opening sentence itself when it is one; and a clause
    of the whole answer for an answer that is a single sentence.

    The cut comes first only for a long sentence, because "In short:" in front of a sentence the
    length of a paragraph is not a short form of anything: "Defrost it when the ice is more than
    about 5mm thick: switch it off at the wall, move the food into a cool box, and leave bowls of
    hot water inside with the door shut." was handed back whole behind the frame at 37 words, where
    the answer two turns up says "I said: Defrost it when the ice is more than about 5mm thick."
    A sentence short enough to be read again is kept whole even when it has a colon in it, because
    its own opening is what a person who did not follow it needs ("A cold stays in the nose and
    throat: a runny nose, sneezing, a sore throat" says more than "A cold stays in the nose and
    throat."). A clause is only taken when it is a real one - "The things that work: same wake-up
    time every day..." opens on a label, and handing back "In short: The things that work." is the
    label and none of the answer.

    Only the answer's own words, in their own order, so a shortened answer cannot be wrong in a
    way the long one was not.
    """
    said = " ".join(str(said or "").split())
    if not said:
        return ""
    lead = _past_a_lead_in(said)
    first = _first_sentence(lead)
    if first:
        doing = _the_doing_of(first)
        if doing:
            return doing
        clause = _a_clause_of(first)
        if len(first.split()) > _A_LONG_SENTENCE:
            if clause and len(clause.split()) * _A_STRIDE <= len(first.split()):
                return clause
            if lead != " ".join(said.split()):
                # A lead-in sentence was stepped over to get here, so what the answer would
                # otherwise come back as is the label that was stepped over ("Take it in this
                # order."): the sentence under it is the answer and is worth the words.
                return _end_a_sentence(first)
            # A long sentence whose cut is not a stride before the rest of it: the half left behind
            # is usually the fix ("uneven load" is the cause, "stop it, undo the tangle" is what to
            # do), so nothing is cut and nothing is claimed. Handing the whole 30-odd words back
            # behind "In short:" is longer than what the person read and no short form of anything.
            return ""
        elif clause and len(clause.split()) * 2 >= len(first.split()):
            # A sentence short enough to read again, with a colon in it: what comes after the colon
            # is the reason or the detail, and the answer's firm side is what is left of it. The
            # colon cut is taken when it is at least half the sentence - "Keep bread at room
            # temperature in a paper bag or a bread bin, not the fridge: the cold makes it go stale
            # faster" is the answer and the reason - and left alone when it is the shorter half,
            # where the cut is the answer's own heading and the list after it is the answer ("A
            # cold stays in the nose and throat: a runny nose, sneezing, a sore throat").
            return clause
        if len(first.split()) <= AGAIN_WORDS:
            return _end_a_sentence(first)
        return clause
    return _a_clause_of(_past_a_lead_in(said))


def _past_a_lead_in(said):
    """The answer without a lead-in sentence in front of it, which is a label and not the answer.

    "Take it in this order. First clear any credit card..." hands back "In short: Take it in this
    order." when the lead-in is read as the opening: five words that say what the answer is about
    to do and none of it. A short opening sentence with more after it is stepped over, so the
    sentence under it is the one kept.
    """
    parts = [part.strip() for part in END_OF_SENTENCE.split(said) if part.strip()]
    if len(parts) < 2:
        return said
    if len(parts[0].split()) >= _A_CLAUSE_LEAST + 2:
        return said
    return said[len(parts[0]):].strip()


def _end_a_sentence(text):
    """The sentence with its full stop, so the frame in front of it reads as a sentence."""
    text = (text or "").strip().rstrip(",;:- ")
    if not text:
        return ""
    return text if text[-1] in ".!?" else text + "."


def _a_clause_of(sentence):
    """The first real clause of one long sentence, or "" when it has none worth handing over."""
    sentence = (sentence or "").strip()
    for match in CLAUSE_END.finditer(sentence):
        cut = sentence[:match.start()].strip().rstrip(",;:-\u2014 ")
        if len(cut.split()) < _A_CLAUSE_LEAST + 2:
            # Six or seven words on the left of a colon is often the answer's own subject said
            # back ("Cream or soured cream going spare: stir it into a chilli...") - a label, not
            # the thing. The cut has to carry a real clause of its own.
            continue
        if not _brackets_closed(cut):
            # The colon or semicolon was inside a bracket, so the cut stops in the middle of one:
            # "Put the cursor under the column and press AutoSum (Alt and = in Excel" is not a
            # clause of anything. Half a bracket never reads as a short form.
            continue
        if not _carries_a_verb(cut) or _leans_back(cut):
            # A cut is read on its own, so a list of places is not a short form of anything and a
            # half that points back at what was cut off names nothing.
            continue
        if _points_at_what_follows(cut):
            # A short opening that ends pointing at the list the colon introduces is the label of
            # that list and not the answer: "Three lines cover most of it." names nothing, where
            # the answer's own first sentence says what the three lines are.
            continue
        return _end_a_sentence(cut)
    return ""


def _the_doing_of(sentence):
    """The half after the sentence's colon when that half is what to do, or "" otherwise.

    Read before the opening cut, because the stride rule below asks whether the opening half is
    enough of the sentence to stand for it - and the half that says what to do is the answer to
    "what?" at any length, which is the opposite of the opening half.
    """
    sentence = (sentence or "").strip()
    for match in CLAUSE_END.finditer(sentence):
        cut = sentence[:match.start()].strip().rstrip(",;:-\u2014 ")
        if len(cut.split()) < _A_CLAUSE_LEAST + 2:
            continue
        if not _brackets_closed(cut):
            continue
        if _points_at_what_follows(cut):
            continue
        return _end_a_sentence(_the_half_that_does_it(cut, sentence[match.end():]))
    return ""


# A sentence cut at a colon can hold its answer on either side, and "what?" is a person who has
# not followed it: "Heating and hot water are most of the bill, so start there: turn the boiler
# flow to 55 to 60C..." answered as its own opening tells the diagnosis twice and drops the
# step, the number and the doing. The verbs that make a half a thing to do rather than a thing to
# know are the ones a person would type back as an instruction, and only in the half's first three
# words: "another.DO_THIS" matches anywhere in a sentence and reads "if", "so" and "worth" as doing
# too, which would make a statement ("it is worth repairing while the quote is under half") a step.
_A_DOING = re.compile(
    r"\b(?:turn|switch|take|keep|put|use|try|check|give|add|buy|swap|replace|clean|wash|rinse|"
    r"leave|stand|wrap|store|feed|water|encourage|bleed|call|ask|book|avoid|stop|start|run|set|"
    r"hold|move|cover|cut|open|close|repeat|ring|email|text|pick|press|fill|mix|stir|boil|blot|"
    r"pour|write|say|tell|offer|lower|heat|defrost|freeze|lock|shut|prick|scrub|soak|scrape|"
    r"wipe|sweep|vacuum|iron|sand|seal|tape|glue|screw|drill|tie|hang|fold|chop|slice|drain|"
    r"compare|measure|weigh|test|log|track|budget|plan|read|learn|practise|split|share|anchor|"
    r"aim|ask|check|brush|clear|empty|refill|label|freeze|work|go|look|listen|watch|wait|sit|"
    r"step|point|answer|name|note|mark|count|sort|tidy|eat|drink|cook|bake|grill|roast|serve|"
    r"pack|carry|lift|bend|stretch|breathe|rest|get|give|help|do|redo|rub|polish|dry|spray|"
    r"apply|dab|swab|wax|shampoo|polish)\b",
    re.IGNORECASE)
# A half that opens on a thing to do is not replaced by the half after the colon: "Take away the
# food and the easy way in: bins with clipped lids..." answered as the list is a fragment and no
# instruction at all.
_A_DOING_WINDOW = 3
# A figure is what an answer that is asked "how much", "how long" or "when" is for: the dates in
# "Titanic was built in Belfast by Harland and Wolff: laid down in March 1909..." are the answer
# to when, and the city is not.
_A_FIGURE = re.compile(
    r"\d|\b(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|twenty|thirty|"
    r"forty|fifty|half|quarter|once|twice|per ?cent)\b", re.IGNORECASE)


# The words a step can open on before the verb itself ("on gas, turn the boiler flow down",
# "for a stain, blot it"), which are not the doing but do not stop the next word being one.
_A_LEAD_IN = frozenset("""on for in with at to from after before if when once and then also""".split())


def _opens_a_doing(half):
    """True when the half opens on a thing to do rather than on a thing to know.

    The first word is what is read, not any word in the first three: "warm tyres read a few psi
    high" is a statement with the verb "read" in it, and handing it back as the step for "how do i
    check my tyre pressure" is the reason rather than the answer.
    """
    words = re.findall(r"[a-z']+", str(half or "").lower())
    if not words:
        return False
    if _A_DOING.fullmatch(words[0]):
        return True
    if words[0] in _A_LEAD_IN:
        return any(_A_DOING.fullmatch(word) for word in words[1:_A_DOING_WINDOW + 2])
    return False


# A colon half that is a clause about the thing - "the thin film stops the steam forming droplets",
# "a little washing-up liquid is fine, but soaking it is what strips the seasoning" - is the reason
# for the opening, not the particulars of it, so it is not handed over in place of an opening that
# is itself an instruction. The test is the whole of the first clause: a list of things has no verb
# in it ("clothes in the three to six month size", "40 to 50m", "Settings > Battery"), and a clause
# about them has one.
_SAYS_HOW = re.compile(
    r"\b(?:is|are|was|were|has|have|had|does|do|will|would|can|could|wants?|needs?|keeps?|"
    r"stops?|strips?|holds?|works?|matters?|helps?|makes?|means?|costs?|takes?|gets?|gives?|"
    r"comes?|stays?|lasts?)\b", re.IGNORECASE)


def _says_how_it_works(half):
    """True when a colon half is a clause about the thing rather than a list of the things."""
    first = re.split(r"[,;]", str(half or ""))[0]
    return bool(_SAYS_HOW.search(first) or _VERB_SHAPE.search(first))


# A half that opens on a thing to do can still name nothing: "Write it in this order and the marks
# look after themselves" is the heading of the list after the colon, and handing it back is the one
# thing the person who typed "what?" already has.
_ANNOUNCES = re.compile(
    r"\b(?:it|them|these|those|this|that)\b(?:\s+[\w'-]+){0,2}\s+(?:order|list|steps?|way|shape)\b",
    re.IGNORECASE)


def _announces_the_list(half):
    """True when a half is a heading for the list in the other half rather than the doing itself."""
    return bool(_ANNOUNCES.search(half or ""))


# The words that make a half lean on the half before it.
_NEEDS_A_SUBJECT = re.compile(
    r"^(?:he|she|it|they|them|this|that|these|those|his|her|their|its|itself|themselves)\b", re.I)
# A past participle opens a phrase about the thing before it, not a sentence of its own.
_A_PARTICIPLE = frozenset("""laid launched built made given taken held written born grown founded
opened designed painted published signed set sold bought won lost sent kept left put begun""".split())


def _needs_its_subject(after):
    """True when a half cannot stand alone as a short form: it opens on a pronoun or a participle."""
    words = str(after or "").split()
    if not words:
        return True
    if _NEEDS_A_SUBJECT.match(words[0]):
        return True
    first = re.sub(r"[^a-z]", "", words[0].lower())
    return first in _A_PARTICIPLE and first not in ("set", "left", "put", "lost")


# A short form is read on its own, so a half with no verb in it at all is a fragment however long
# it is: "In the fridge, on a plate on the bottom shelf" answers nothing, and the answer to "how do
# i defrost mince in the microwave" went there because a place is not a sentence.
_VERB_SHAPE = re.compile(r"\b\w{4,}(?:ed|ing)\b", re.I)
_A_VERB = frozenset("""is are was were be been am has have had do does did can could will would
should must might may need needs want wants take takes give gives make makes keep keeps leave
leaves put puts get gets add adds use uses turn turns go goes come comes cost costs last lasts
help helps hold holds cut cuts run runs set sets let lets seem seems feel feels work works mean
means change changes choose chooses find finds show shows matter matters depend depends ring
rings wash washes clean cleans""".split())
# A statement of cause opens on one of these, and a verbless half that does is the diagnosis
# itself: "Nearly always the air pocket at the fat end" is the answer to why the eggs crack.
_A_CAUSE_OPENS = re.compile(
    r"^(?:nearly|usually|mostly|often|almost|probably|generally|mainly|sometimes|always|never|"
    r"rarely|hardly)\b", re.I)


def _carries_a_verb(half):
    """True when a half is a sentence rather than a list of places or things."""
    text = str(half or "")
    if not text.strip():
        return False
    if _A_DOING.search(text) or _VERB_SHAPE.search(text):
        return True
    if any(word in _A_VERB for word in re.findall(r"[a-z']+", text.lower())):
        return True
    if _A_FIGURE.search(text):
        # A verbless half that carries the figure is the answer to "how much" or "how long": "A
        # pound or two, or round it up" is the amount, and the half after its colon is the reason.
        return True
    return bool(_A_CAUSE_OPENS.match(text))


# A half that points back at the half it was cut from names nothing on its own: "Any of the three
# takes under ten minutes" is the list that was thrown away, "The rest of the skin can wait" is
# what was left behind, and "Prick that end" is an end the half before it named.
_LEANS_BACK = re.compile(
    r"\b(?:them|these|those|both|each|either|neither|the rest|all of (?:the|them)|the others?|"
    r"any of (?:the|them)|that end|this end|this order|these steps|the ones|"
    r"as follows)\b", re.I)


# Six words, the fence bright-fork asked for on #6056: nothing that early in a half can point at
# the half that went and still read on its own. "Both freeze well for up to 3 months" was handed
# back for "how long does chicken keep in the fridge", and both of the things that freeze are in
# the half before the colon.
_LEANS_BACK_WINDOW = 6


def _leans_back(half):
    """True when a half needs the half before it to mean anything.

    Only in its first few words: "work through the examples with the book open, then close it and do
    them again" carries its own "them" - the examples - while "Read them, and if half of them bore
    you" opens on a word with nothing behind it.
    """
    return bool(_LEANS_BACK.search(" ".join(str(half or "").split()[:_LEANS_BACK_WINDOW])))


# The half after a colon that only gives the reason is not the answer to a question that asked what
# to do: "Change it every three months: a worn brush cleans much less well" handed back as "a worn
# brush cleans much less well" tells the person how often a brush wears out, not how often to change
# it. A determiner in front of a noun is how a justification opens.
_EXPLAINS = re.compile(r"^(?:a|an|the|most|some|many|much|which|because|so|that|this)\b", re.I)


# A reason is one short clause standing behind the instruction before it: "a worn brush cleans much
# less well", "warm tyres read a few psi high". Longer than this, or with a comma list in it, the
# half after the colon is not a reason: it is the sizes, the menu path or the distances the opening
# was announcing, and that is what the person who did not follow the answer needs.
_A_REASON_LEAST = 12


def _the_reason(after):
    """True when the half after the colon justifies the half before it rather than completing it."""
    after = str(after or "")
    if len(after.split()) > _A_REASON_LEAST or "," in after or ";" in after:
        return False
    return _carries_a_verb(after)


# A half after the colon that opens on an amount is a worked example of the instruction, not the
# instruction: "Compare the APR and the total repayable rather than the monthly payment: £5,000 at
# 8 per cent over three years comes back as about £5,650" hands back a sum where the person asked
# what to do.
_OPENS_ON_A_FIGURE = re.compile(r"^\s*(?:[£$\u20ac]\s*\d|\d)")


def _opens_on_a_figure(after):
    """True when the half after the colon opens on an amount or a count."""
    return bool(_OPENS_ON_A_FIGURE.match(str(after or "")))


# An opening that names nothing in particular - "Buy the boring things that get used up", "Do it on
# wifi with the phone on charge", "Start further away than you think you need to" - is completed by
# the colon half, which is the sizes, the menu path, the distance. An opening that names its things
# ("Take away the food and the easy way in") is the instruction already, and the colon half is the
# detail of it.
_A_CATEGORY = re.compile(
    r"\b(?:it|them|these|those|things|stuff|bits|ones|kinds|sorts|lots)\b"
    r"|\b(?:need|needs|want|wants|have|has|how|what|where|when|who)\s+to\W*$",
    re.I)


def _names_no_particular(before):
    """True when the opening is general enough that only the colon half says what to do."""
    return bool(_A_CATEGORY.search(before or ""))


def _the_half_that_does_it(before, after):
    """The half of a colon sentence a person who did not follow it needs, or "" for the opening.

    The opening half is kept when it is itself the doing ("Take away the food and the easy way in")
    or when it carries the figure asked for ("A pound or two, or round it up"). The half after the
    colon is handed over when the opening only says what is wrong or what a thing is and the doing
    or the number is on the other side ("A dripping tap is nearly always a worn washer: turn the
    water off at the valve under the sink").
    """
    before = (before or "").strip()
    after = (after or "").strip().rstrip(",;:- ")
    if len(after.split()) < _A_CLAUSE_LEAST // 2:
        return ""
    if not _carries_a_verb(after) or _leans_back(after):
        return ""
    if _needs_its_subject(after):
        # The half after the colon can lean on the half before it: "He ran the government from 1721
        # to 1742" has no first minister in it, and "laid down in March 1909, launched on 31 May
        # 1911" is a participle whose subject went with the opening. A short form has to stand on
        # its own, so a half that opens on a pronoun or a bare participle is not handed over: the
        # opening half is, which does name its subject.
        return ""
    if _opens_a_doing(before) and not _announces_the_list(before):
        if _opens_a_doing(after):
            if len(after.split()) >= len(before.split()):
                # Both halves are things to do, and the opening is the short version of them:
                # "Anchor the wake-up time first and let the bedtime follow" is the plan, and the
                # getting up at the same time every day is how to do it. The half that says how
                # wins when it carries at least as much as the opening; where it is the short tail
                # of a longer method ("blot dry with a towel; repeat until nothing more comes up")
                # the method is the answer.
                return after[:1].upper() + after[1:]
            return ""
        if _the_reason(after) or _opens_on_a_figure(after):
            # The half after the colon justifies the instruction or works an example of it, so the
            # instruction is the answer.
            return ""
        if _A_FIGURE.search(before) and not _opens_on_a_figure(after):
            # The opening carries the amount or the date asked for and the colon half is the reason
            # for it: "A pound or two, or round it up: a hairdresser usually keeps the change" is a
            # figure and its justification, and the figure is the answer.
            return ""
        if not _names_no_particular(before):
            # The opening names the things itself ("Take away the food and the easy way in"), so it
            # is the instruction and the colon half is the detail of it.
            return ""
        # The opening is a general instruction - "Buy the boring things that get used up", "Do it
        # on wifi with the phone on charge", "Start further away than you think you need to" - and
        # the colon half is what it comes to: the sizes, the menu path, the distance. Handing back
        # only the general half leaves the person the plan they already read and none of the
        # particular thing they could act on. Not when the colon half is a clause about the thing
        # instead: "Rub a tiny drop ... then polish it off with a dry cloth: the thin film stops the
        # steam forming droplets" is an instruction and its reason, and the reason is the one half
        # a person who did not follow the instruction cannot use.
        if _says_how_it_works(after):
            return ""
        return after[:1].upper() + after[1:]
    if _opens_a_doing(after):
        if _A_FIGURE.search(before) and not _opens_on_a_figure(before) and not _names_no_particular(before):
            # The opening names the thing and carries the price or the time it takes, and the colon
            # half is a step to take before it: "A brush or rubber strip ... is the cheap fix, about
            # ten pounds and ten minutes: measure the gap first." The price is what was asked for,
            # and "Measure the gap first." on its own is the preamble to the answer, not the answer.
            return ""
        return after[:1].upper() + after[1:]
    if _EXPLAINS.match(after):
        if _A_FIGURE.search(before) and not _opens_on_a_figure(after):
            return ""  # the opening carries the figure asked for, the colon half explains it
        if not _names_no_particular(before):
            return ""  # the opening names the things itself, so it is the instruction
        if _the_reason(after):
            # The half after the colon is the reason for the half before it ("a worn brush cleans
            # much less well"), so the half before it is the answer.
            return ""
        if _carries_a_verb(before):
            # A whole clause after the colon that is not a reason is what the opening named: "it is
            # the shower" is answered by "an electric shower usually wants the pull cord checked",
            # and handing back only "it is the shower" is the diagnosis and none of the fix.
            return after[:1].upper() + after[1:]
        return ""
    if not _A_FIGURE.search(before) and _A_FIGURE.search(after):
        return after[:1].upper() + after[1:]
    return ""


# The words that can stand in for the thing after a colon. Short before them and the cut has
# nothing to point at yet ("Three lines cover most of it:"); long before them, the pointing word
# has its referent already ("fill the kettle just past that:" refers back to the 300 ml).
_POINTS_FORWARD = re.compile(r"\b(?:it|them|these|those)\W*$", re.IGNORECASE)
# A superlative at the end of a cut points at the list after the colon however long the cut is: "for
# the app using the most" names no app until the apps are named.
_POINTS_FORWARD_ANY = re.compile(
    r"\bthe (?:most|best|worst|biggest|main|first|last|rest)\W*$", re.IGNORECASE)
_POINTS_FORWARD_LEAST = 10


def _points_at_what_follows(cut):
    """True when a cut is too short and too vague to be anything but a heading."""
    cut = (cut or "").strip()
    if _POINTS_FORWARD_ANY.search(cut):
        return True
    return bool(_POINTS_FORWARD.search(cut)) and len(cut.split()) < _POINTS_FORWARD_LEAST


def _brackets_closed(text):
    """True when every bracket in `text` is opened and closed in it."""
    text = text or ""
    return (text.count("(") == text.count(")") and text.count("[") == text.count("]"))


def _the_route_is_in_it(said):
    """True when the answer names the way out of it, so no part of it can be handed back alone."""
    return bool(NO_CUT.search(str(said or "")))


def said_again(clean, memory):
    """The reply to a bare "say that again", or None when the line is not one this reads.

    Public because the composer's own repeat pool (`REACTION_REPEAT` in fallback.py) is reached
    first for "what?" and "huh", and there is no reason for it to say a stock "which bit?" when
    the answer above can simply be said shorter. When it cannot be said shorter the turn is left
    to that pool: a stock "which part?" gives the person nothing where the answer's own opening
    would, and the pool's "I said: <the opening>" is the answer's own words.
    """
    if not SAID_AGAIN.match(clean):
        return None
    if _an_answer_to_act_on(_last_turn(memory)):
        # The answer says to act now, so its own words are what the person needs to hear again
        # rather than a shortened form of them: the module that wrote it hands it back whole.
        return None
    short = _not_shortened(_said_above(memory))
    if not short:
        return None
    return pick(AGAIN_SHORTER, memory, clean).replace("{short}", short)


def is_the_answer_shorter(reply, last):
    """True when `reply` is the last answer's own words, shorter, in this module's frame.

    The arbiter's never-repeat rule needs one thing this module knows and it cannot see: whether a
    candidate that would otherwise be passed over is a second telling of the answer or a cut of
    it. Every real candidate on a bare repeat is the answer again ("Sure - <the paragraph>"), and
    the reply this module wrote for the same line is a cut of the same words - so it is the only
    thing on the table that says anything new, and the arbiter may take it where the whole
    paragraph is all that is beside it. Only the module's own frame is recognised and only where
    the words behind it are the answer's own, in their own order, so a stock line that happens to
    share a phrase is never read as a short form of anything.
    """
    text = str(reply or "").strip()
    short = ""
    for lead in REPEAT_LEADS:
        if text.startswith(lead):
            short = text[len(lead):]
            break
    if not short:
        return False
    words = re.findall(r"[a-z0-9']+", short.lower())
    previous = re.findall(r"[a-z0-9']+", str(last or "").lower())
    # Short of the answer by more than a frame's worth of words, so "In short:" is honest, and a
    # run of the answer's own words rather than a paraphrase of them. Where in the answer the run
    # sits is not read: a cut can be the opening sentence or the half a colon introduces, and both
    # are the answer's words in the answer's order.
    if len(words) < 3 or len(previous) < len(words) + 4:
        return False
    size = len(words)
    return any(previous[start:start + size] == words
               for start in range(0, len(previous) - size + 1))


def _said_above(memory):
    """The answer the person is asking about, or "" when there is not one.

    An answer that is itself a repeat ("From just now: Titanic was built in Belfast...") is read
    for what it says, not for the frame it came in: shortening the framed line stacked one frame
    on another ("The gist of it: From just now: Titanic was built in Belfast").
    """
    last = _last_turn(memory)
    return _unframed(str(last.get("bot") or ""))


def _unframed(reply):
    """The answer under a repeat's lead-in ("From just now: ...", "You've got it: ...").

    Every module that hands an answer back puts a lead-in in front of it, and none of those leads
    is part of the answer: shortening the framed line stacked one frame on another ("The gist of
    it: From just now: Titanic was built in Belfast"). `bot/memory/another.FRAME` is the one place
    that reads those leads, so this asks it rather than keeping a list of its own.
    """
    reply = str(reply or "")
    for lead in REPEAT_LEADS:
        if reply.startswith(lead) and reply[len(lead):].strip():
            # This module's own frame: saying the short form shorter again said nothing.
            return reply[len(lead):].strip()
    found = another.FRAME.match(reply)
    if found and reply[found.end():].strip():
        return reply[found.end():].strip()
    return again.unframed(reply) or reply


def _not_shortened(said):
    """The answer said shorter, or "" when the answer is not this module's to shorten.

    The four kinds left alone are the answer that says to act now (its own words are what the
    person needs), the answer that opens by taking bad news in (a condolence said shorter reads as
    a form letter), the answer that names the way out (the opening is the harmless half and the
    route is the sentence that matters), and the answer with nothing in it to cut.
    """
    said = str(said or "")
    if len(said.split()) < ANSWER_LONG:
        return ""
    if CARE_ANSWER.search(said) or OPENS_ON_CARE.match(_first_sentence(said) or said):
        return ""
    if _the_route_is_in_it(said):
        return ""
    short = _a_shorter_way(said)
    # What the answer would otherwise come back as: its own opening sentence, which is what every
    # module's repeat hands over. A form that only takes the frame off that sentence is the same
    # words with a new label on them. A step over a lead-in sentence is exempt: there the echo is a
    # label ("Take it in this order.") and the sentence under it is the answer whatever its length.
    echo = _first_sentence(_past_a_lead_in(said)) or said
    doing = _end_a_sentence(_the_doing_of(echo))
    if doing and short == doing:
        # The half after the colon is handed over where the opening only says what is wrong ("A
        # dripping tap is nearly always a worn washer: turn the water off..."). What the person
        # already read is the whole answer, not just its opening, so that is what the saving is
        # counted against: the words left behind are the diagnosis they have had once already.
        echo = said
    saved = len(echo.split()) - len(short.split()) if short else 0
    if _past_a_lead_in(said) == " ".join(str(said or "").split()) and \
            saved < max(_A_SAVE_LEAST, len(echo.split()) // 4):
        # "In short:" in front of the answer is the frame claiming a short form it does not deliver:
        # the person is handed the same words with a new label on them, which is the one thing they
        # already knew when they typed "what?". A couple of words off a sentence is the same words,
        # so nothing is claimed and the module that wrote the answer hands it back the way it
        # always did - which is also what keeps this module from ever growing a reply.
        return ""
    return short


def takes_as_it_comes(text, memory):
    """Read by the arbiter: on a bare "why" after an answer, the reason is this module's turn.

    The line has no words of its own, so the module that answered first owns it by default and its
    follow-up path hands the answer above back - "Same as before: <the whole paragraph>". That
    paragraph is what the person just read, so nothing in it answers the line they typed. This
    module reads that turn and gives the cause out of it, or says it cannot see one and asks, so
    the arbiter asks for this declaration before the never-repeat fallback (README.md,
    "Interface"). It says no to every line that is not a bare why after a substantive answer.

    A card that warns of harm in the next few minutes is not claimed either, so the module that
    wrote it hands it back whole (see `respond`). A card that says "the same day" is claimed: it is
    the ordinary GP-this-week answer, and stepping aside for it handed the paragraph back.

    Everything else is claimed even when no reason can be read out of the answer above, because
    the alternative is not silence: the module that answered first hands its own answer back as
    "Same as before: <the whole paragraph>", which is the paragraph the person just read. That
    echo is what this claim exists to stop (it is the one reply the repeat fallback cannot see).
    """
    clean = " ".join(str(text or "").lower().split())
    if SAID_AGAIN.match(clean):
        # "what?" is the same claim with a different reply: the answer above is the only place a
        # shorter form of it can come from, and every module that would hand it back hands back
        # the paragraph the person says they did not follow. A warning is not shortened, so that
        # one is left where it is.
        if _an_answer_to_act_on(_last_turn(memory)):
            return False
        if not _not_shortened(_said_above(memory)):
            # Nothing this module can make shorter - a health answer, a condolence, a sentence
            # with no clause in it to cut at - so the turn stays with the module that wrote the
            # answer and it hands the answer back the way it always did.
            return False
        return True
    if not _is_bare_why(clean):
        return False
    last = _last_turn(memory)
    if _an_answer_to_act_on(last):
        return False  # the warning is the answer, and the module that gave it hands it back
    if _said_the_reason_cannot_be_seen(memory):
        # The answer above is this module's own shrug, so there is nothing in it to narrow: the
        # length floor is there to leave a short answer to the knowledge module's "the newest
        # sentence it has", and a shrug has no newest sentence. Left unclaimed, "why" twice in a
        # row read the shrug and handed back the card under it word for word.
        return True
    return len(str(last.get("bot") or "").split()) >= ANSWER_LONG


# "Why do you say that", "why did you say so", "how come you said that", "what makes you say
# that": the words ask about the answer just given, so it is the same ask as a bare "why" in more
# words. Nothing here matched them, so the composer answered a different question - "No grand
# reason. Someone built a thing that helps with everyday questions without a search engine" -
# which is why the bot exists, not why it said what it said. "Think" is left out on purpose:
# "why do you think that" asks how its mind works, and that has an answer of its own.
WHY_YOU_SAID_IT = re.compile(
    r"^(?:(?:but|and|so|ok|okay|yeah|no|well|right)\s+)*"
    r"(?:"
    r"(?:why|y|how come)\s+(?:(?:do|did|would|will|are|were)\s+)?(?:you|u)\s+"
    r"(?:say|saying|said|tell me|told me|reckon|claim)"
    r"|what\s+makes\s+(?:you|u)\s+say"
    r"|why\s+(?:do\s+you\s+|would\s+you\s+)?think"
    r")\s+(?:that|this|so|it|those|these)"
    r"(?:\s+is)?(?:\s+(?:then|though|tho))?[\s?!.,]*$",
    re.IGNORECASE)
# ...and a line that asks the reason for the bot's own words is the same ask whichever module
# wrote the answer above it. "why do you say that" under a knowledge card is `_last_turn`'s job,
# but under a line about what the bot is ("asking a program what it makes of you is a stretch",
# "no feelings to check, so nothing to report on my side") the answer above is one of the
# fallback's own pools, not one of the ANSWERED modules, so `_last_turn` held out and the ask fell
# through to the search hedge - "that's beyond what I know well, sorry" under a line the bot was
# certain of. The reason owed in those turns is the bot's own, the same reason `WHY_THE_BOT` gives,
# so the bot's last line is read for its own make-up as well as the user's line above.
THE_BOT_DESCRIBED_ITSELF = re.compile(
    r"\b(?:a program|a chatbot|a bot|not a person|no feelings|nothing in me|just rules|"
    r"written rules|rules someone wrote|rules doing their job|no mind behind|behind the "
    r"curtain|nothing to report on my side|no inner)\b",
    re.IGNORECASE)
# The line the answer above replied to, when it was about the bot itself: "do you have feelings",
# "are you a person", "tell me about yourself", "you are a bot". A saying ask after one of those
# asks why the bot says it has no feelings, and that is the one reason the bot can give from its
# own side. The second person is what makes the line about the bot rather than about the world.
#
# The reason is said here rather than handed back to the identity pool, which was the first shape
# of this: that pool's own reading moved on, and a line it no longer takes falls through to the
# search hedge - "that's beyond what I know well, sorry" under a bot that had just described
# itself. A stand-down has to name where it stands down to, and there was nothing left there.
# An answer that was care - a condolence, an apology, "be gentle with yourself" - has no cause
# inside it to hand back. "why do you say that" after one is asking whether the bot meant it, so
# the answer says that it did, and claims nothing about the world. The phrases are the bot's own:
# they are what the care pools actually say, and the greeting, loss and safety modules all write
# them. Without this the turn was the search hedge, which reads worse after a condolence than
# anywhere else in the conversation.
CARE_ANSWER = re.compile(
    r"\b(?:i'?m (?:really |so )?sorry|so sorry|sorry to hear|sorry about|a real loss|"
    r"be gentle with yourself|no words needed|you did the right thing|i'?m here for you|"
    r"here if you want|nothing you have to say|how are you (?:holding up|doing))\b",
    re.IGNORECASE)
WHY_CARE = (
    "Nothing behind it: you told me something hard, and I meant it.",
    "No reason beyond what you said - I'm sorry, and I still mean it.",
    "There's nothing to work out in it: you said something hard, and that was enough for me to "
    "be sorry about it.",
)
WHY_THE_BOT = (
    "Because there is nothing in here to feel it with: I'm rules someone wrote for ordinary "
    "questions, and the words come from those rather than from anything I have lived.",
    "Because that is all I am made of - written rules. Nothing in me feels something first and "
    "reports it after, so there is no inner reason behind the line.",
    "Because there is no machinery for it in here, which is the whole of the answer: I pick the "
    "words from what is written into me and from what you have told me here.",
)
ABOUT_THE_BOT_LINE = re.compile(
    r"^\W*(?:(?:so|ok|okay|and|but|well|right|hey|hi)\s+)*"
    r"(?:(?:are|do|did|does|can|could|would|will|have|has|were|is)\s+(?:you|u|ya)\b"
    r"|(?:you|u)\s+(?:are|re)\b"
    r"|tell me about yourself\b|what are you\b|who are you\b|what do you do\b)",
    re.IGNORECASE)


def asks_about_the_last_answer(clean):
    """True when the line asks about the words the bot just used ("why do you say that")."""
    return bool(WHY_YOU_SAID_IT.match((clean or "").strip()))


def respond_to_a_saying_ask(clean, memory, understood=None, body=False):
    """The reply to "why do you say that", or None when the line is not one of those.

    It is the bare ask in more words, so the answer is the bare ask's answer: the reason read out
    of the turn above. The one turn that gets its own reason is a saying ask about an answer that
    described the bot itself: the reason asked for is the bot's own, and it is said from here
    rather than left to a pool that no longer reads the line (see WHY_THE_BOT).

    Two answers do not come out of the reason reading, and both are named here rather than handed
    back to whatever is left, because what is left is the search hedge ("that's beyond what I know
    well, sorry"): an answer that described the bot (WHY_THE_BOT) and an answer that was care
    (WHY_CARE). Everything else is the reason, and when the answer above names no cause at all the
    turn is left exactly as it was rather than turned into "which part of that do you want the why
    for?" - a shove at a person who has just been told a fact they did not ask about.

    Half of the composer's work is done before this function is reached: a line that says what it
    is asking about ("why did you say that about my sister") is not this ask at all, and the pool
    for a question about the bot answers the rest.
    """
    # "Why do you think that", "why do you think so": the same ask as "why do you say that" once
    # there is an answer on the screen, and the bot-about card answered it with a paragraph about
    # there being no mind behind it - a question about the bread, answered about the machine. It is
    # read here rather than in `asks_about_the_last_answer` because with nothing said it is not
    # this ask at all: there is no answer to give a reason for, and the bot's make-up is the
    # right reply. So it stands down where there is no answer above and the card keeps the turn.
    if THINKS_BACK.match((clean or "").strip()):
        if not _the_turn_above(memory).get("bot"):
            return None
        return respond(clean, memory, understood, body=body)
    if not asks_about_the_last_answer(clean):
        return None
    # The turn above is read as it is, not through `_last_turn`: that one holds out for an answer
    # that made a claim (a reason can only come out of one), and the reason for describing itself
    # is the bot's make-up, which needs no claim under it. Read through `_last_turn`, the two
    # shortest identity answers ("I'm a chatbot - here to help and chat") fell through to the
    # search hedge while the longer one got the reason, which is a length deciding the reply.
    said = str(_the_turn_above(memory).get("user") or "")
    if ABOUT_THE_BOT_LINE.match(said):
        return pick(WHY_THE_BOT, memory, clean)
    above = str(_the_turn_above(memory).get("bot") or "")
    if CARE_ANSWER.search(above):
        return pick(WHY_CARE, memory, clean)
    if THE_BOT_DESCRIBED_ITSELF.search(above):
        return pick(WHY_THE_BOT, memory, clean)
    last = _last_turn(memory)
    if not last:
        return None
    if not _reason_in(last):
        # The answer above names no cause, so there is no reason to hand back - and the turn fell
        # to the search punt ("that's beyond what I know well, sorry") under a bot that had just
        # answered the question, which reads worse than the answer itself. The answer is still the
        # answer, so it goes back framed as the repeat it is, in the memory store's own words
        # (`topics.said_again`, which is where "Same as before:" lives). Before the answers module
        # started passing its line to that helper (#6335) this reply came from there.
        from ..memory import topics
        return topics.said_again(str(_the_turn_above(memory).get("bot") or ""), memory)
    return respond("why", memory, understood, body=body)


def _the_turn_above(memory):
    """The last turn, whatever module answered it, or {} when there is none."""
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list) or not turns:
        return {}
    last = turns[-1]
    return last if isinstance(last, dict) else {}


def respond(clean, memory, understood=None, body=False):
    """The reply to a bare "why" follow-up, or None when the line is not one.

    `clean` is the tidied line, `memory` the conversation so far and `body` the caller's reading
    of whether the last few lines were about their body. `understood` is unused here and kept so
    every composer helper takes the same call shape.
    """
    again = said_again(clean, memory)
    if again:
        return again
    thinks_back = bool(THINKS_BACK.match((clean or "").strip()))
    if not (_is_bare_why(clean) or thinks_back):
        return None
    last = _last_turn(memory)
    if not last:
        if THE_BOT_DESCRIBED_ITSELF.search(str(_the_turn_above(memory).get("bot") or "")):
            # A bare "why" under a line about what the bot is gets the bot's own reason, the
            # same one the saying ask on top of it gets. Without this the line reached the search
            # hedge, which says the subject is beyond the bot when the subject is the bot.
            return pick(WHY_THE_BOT, memory, clean)
        if _said_the_reason_cannot_be_seen(memory):
            return pick(WHY_AGAIN, memory, clean)
        return None
    # The answer above warns of harm that is minutes away, so the person is owed that answer
    # rather than the reason cut out of it: "Pull over, switch the engine off" is the reply to
    # "what is causing it" when the engine is overheating. It is not claimed either (see
    # `takes_as_it_comes`), so the module that wrote the card hands it back whole. A "same day"
    # tail is not that: it is the GP-this-week phrasing of 87 answers, and standing aside for it
    # gave back the paragraph with "Same as before" in front (hardy-pen, #3685).
    #
    # What this module must not do is go quiet: a decline with nothing left to propose is worse
    # than the shrug it replaced. "i keep getting headaches" / "why does that happen" is a card
    # with a warning in its tail, and saying nothing there handed the turn to the search
    # punt (hardy-pen, spry-ring). A card is not read for a reason, but the question is still
    # answered honestly - the same shrug an answer that names no cause gets.
    act_now = _an_answer_to_act_on(last)
    # "what is causing it" and "what am i doing wrong" both ask about the whole answer, so neither
    # gets "which part of that do you want the why for?" back: the line has already said it is all
    # of it. The reason is read strictly for both, because the cause of one step is not the cause.
    whole_thing = bool(WRONG.search(clean) or CAUSING_IT.search(clean))
    if WHY_NOT.search(clean):
        # "should i drink coffee before bed" / "why not" was told "I can't tell why not from here"
        # while the bot's own answer opened "It is the caffeine: ...". Only a cause the answer
        # names outright is quoted, because an ordinary "because" clause in an answer is usually
        # the reason to do the thing ("because those are £50 to £150 and give you years more
        # use"), and said back as a reason not to it is the opposite of the answer.
        reason = "" if act_now else _a_cause_named_outright(last)
        if not reason:
            # No cause on the face of the answer, so the question is about the advice itself:
            # "try couch to 5k" / "why not" is asking why the bot would have it that way, and an
            # answer about a third party's motives invents a person. It is a third party only
            # when the person's own line named one deciding something.
            if _about_someone_elses_decision(memory):
                return pick(WHY_NOT_ANSWERED, memory, clean)
            if _the_suggestion_was_theirs(memory):
                return pick(WHY_NOT_ITS_OWN, memory, clean)
            return pick(WHY_NOT_ANSWERED, memory, clean)
    else:
        reason = "" if act_now else _reason_in(last, strict=whole_thing)
    if reason:
        said = reason[len("because "):] if reason.lower().startswith("because ") else reason
        if _named_as_a_sentence(last, said):
            pool = WHY_NAMED_SELF
        else:
            pool = WHY_NAMED_BECAUSE if said is not reason else WHY_NAMED
        reply = _in_frame(pick(pool, memory, clean), said)
        reply = reply if reply.endswith((".", "!", "?")) else reply + "."
        # The reply is the answer's own words, so the answer is still what the next follow-up is
        # about: "what could be causing it" then "is it dangerous" has to reach the verdict
        # reader (bot/compose/verdict.py) with the knowledge answer behind it, and the recorded
        # module for this line is whoever proposed it, not the knowledge base (hearty-emu, #2912).
        reply = reply[0].upper() + reply[1:]
        return reply
    if thinks_back and not act_now:
        # This one ask is aimed at the bot's own reasoning, so where the answer names no cause the
        # answer is the reason it can stand behind, handed back as the repeat it is - the same
        # reply "why do you say that" gets above. "I don't know why, and I'd rather say so than
        # invent one" under an answer the bot has just written reads as the bot disowning it, and
        # the question it carries ("what happens just before it goes wrong") is about a fault:
        # after "how do i stop my bread going mouldy" there is no fault to describe.
        from ..memory import topics
        handed_back = topics.said_again(str(_the_turn_above(memory).get("bot") or ""), memory)
        if handed_back:
            return handed_back
    if body:
        return pick(WHY_BODY, memory, clean)
    if not act_now and whole_thing and _gave_a_method(last) and _reads_a_fault(last):
        # "my sister isnt talking to me" / "whats wrong" got "tell me what it does and I'll work
        # it back from that": the same machine words as the loaf, on a person. The guard is the
        # one the thirds already have - a line about a life has no process in it to stand behind
        # (cobalt-ivy, red-beaver, #3685) - and the honest reply there is the shrug below that
        # asks what happened.
        # Only a whole-answer ask: "what am i doing wrong" is the person saying the whole thing
        # went wrong, and if the answer above was steps with no cause in it, the honest reply
        # names the half the bot can stand behind. A bare "why" keeps the shrug it has always had.
        return pick(WHY_METHOD, memory, clean)
    if whole_thing:
        pool = WRONG_ANSWERED if _reads_a_fault(last) else WRONG_NOT_A_FAULT
        return pick(pool, memory, clean)
    return pick(WHY_ANSWERED, memory, clean)
