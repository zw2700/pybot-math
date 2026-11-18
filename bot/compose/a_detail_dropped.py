"""The person has said something, and the bot answers with an acknowledgement and no next step.

Two replies in the composer are a receipt rather than a reply, and they are what a line that
*says* something instead of asking gets on main:

    my brakes feel spongy on my bike   -> "I'm listening - say more if it helps."
    my rent is 800                     -> "Got it. Is there anything you'd like a hand with?"
    its the lower back, mostly on the right
                                       -> "Got it. Is there anything you'd like a hand with?"
    the family is coming over on sunday
                                       -> "Got it. Is there anything you'd like a hand with?"

A receipt is right for small talk and wrong for all of these: a thing that is failing, a figure
about their own money, a detail about a body, a day with something on. Nobody who says "my brakes
feel spongy" wants to hear that the bot is listening; they want the next thing to check. Nothing
has to be looked up to answer any of them, which is why the hedge is not the excuse.

So this file turns the receipt into one short question about the thing they just said - the
question a friend asks to be useful rather than to be polite. It is the move STYLE.md asks for
when the bot cannot answer the whole question: say what is known, then ask the one thing that
narrows it.

It is a last resort, and written to be one. `bot/modules/greeting.py` asks it after every reader
that knows a subject, and it only takes the turn when the reply the composer chose is one of its
two receipts, so an answer of any kind keeps the turn it has. It never states a fact and never
names a figure of its own: the question is made from the person's words.

Kinds are tried narrowest first: a figure about their money, a detail about a body, a thing that
is failing, a day with something on, and a decision with two ways out.
"""
import re

from . import pick

# The three receipts this file may replace, which are the NEUTRAL pool in bot/compose/fallback_data. Anything else - a card, a pool reply, the search
# hedge - was chosen by a reader that knows something, and keeps the turn.
A_RECEIPT = re.compile(
    r"\bis there anything you'?d like a hand with\b|\bsay more if it helps\b|"
    r"\bthanks for telling me\b[^.]{0,40}\bdig into any of that\b", re.I)

# A question is not a detail dropped: the ask door answers a question, and a receipt there is
# the small talk pool doing its job.
QUESTION = re.compile(
    r"^\W*(?:is|isnt|isn't|are|arent|aren't|was|wasnt|wasn't|were|do|does|did|can|could|will|would|"
    r"should|shall|may|might|have|has|had|who|what|when|where|why|how|which|whose)\b")

# Lines that are a greeting, a thank you, a yes/no, or a shrug of their own: the receipt is the
# right reply to all of them, and asking a question about "ok then" is not.
A_SMALL_LINE = re.compile(
    r"^(?:hi|hiya|hey|hello|yo|good morning|morning|good evening|evening|thanks|thank you|ta|"
    r"cheers|ok|okay|k|kk|cool|right|fine|yes|yeah|yep|no|nope|nah|not really|maybe|sure|"
    r"alright|fair enough|lol|ha|haha|hmm+|oh|ah|i see|got it|nice|great|good|sound)\b"
    r"[\s,.!?]*(?:\w+(?:\s+\w+){0,2})?$")

# A figure of their own: "2400", "£2,400", "about 2400", "45k", "my rent is 800", "pay is 30k".
A_FIGURE_ALONE = re.compile(
    r"^\W*(?:(?:about|around|roughly|near|just|only|maybe|probably|i think|its|it's|thats|"
    r"that's|like|so)\s*)*(?:£|\$|eur|euros?\s*)?"
    r"\d[\d,\.]*\s*(?:k|grand|thousand|a month|a week|a year|per month|per week|per year|pm|pcm|"
    r"pounds?|quid)?\W*$")
A_FIGURE_THEIRS = re.compile(
    r"\b(?:my|our)\s+(?:[a-z']+\s+)?"
    r"(rent|mortgage|salary|pay|wage|wages|income|pension|budget|bill|bills|loan|savings|"
    r"overdraft|deposit)\b(?:\s+(?:is|was|are|comes to|went up to|now))?\s*"
    r"(?:about|around|roughly|only|just)?\s*(?:£|\$|eur\s*)?\d[\d,\.]*\s*(?:k|grand|thousand)?")

# A part of their body, said with something that narrows it (a side, a time, a quality).
A_BODY_PART = re.compile(
    r"\b(?:my|the)\s+(?:[a-z']+\s+)?"
    r"(back|knee|knees|hip|shoulder|neck|stomach|tummy|head|headache|ankle|wrist|elbow|chest|"
    r"tooth|teeth|throat|ear|ears|eye|eyes|leg|legs|arm|arms|foot|feet|toe|toes|heel|skin|"
    r"sinus|joint|joints|gut|bladder|period|periods)\b"
    r"|\bits\s+(?:the\s+)?(?:[a-z']+\s+)?(?:back|knee|hip|shoulder|neck|stomach|head|ankle|"
    r"wrist|elbow|chest|foot|leg|arm)\b")
# How a body part is described when it is the whole point of the line.
A_BODY_QUALIFIER = re.compile(
    r"\b(?:lower|upper|left|right|both|sore|stiff|aching|achy|throbbing|sharp|dull|burning|"
    r"swollen|tender|hurts?|hurting|killing me|giving way|gives way|clicking|locking|numb|"
    r"tingling|stabbing|on the right|on the left|mostly|worse in the morning|at night)\b")

# A thing of theirs that is not working, blocked, or turning up where it should not.
A_THING_FAILING = re.compile(
    r"\b(?:clogged|clogging|blocked|blocking|leaking|leak|broken|broke|knackered|faulty|"
    r"not working|wont work|won't work|wont start|won't start|wont turn on|stopped working|"
    r"packed in|given up|spongy|squeaking|squealing|rattling|smells?|smelly|damp|mould|mold|"
    r"flies|ants|mice|rats|flies everywhere|beeping|flashing|jam|jammed|stuck|flooded|flooding|"
    r"waterlogged|sodden|rotting|rusting|overflowing)\b")
# Sitting on something that belongs to a person: "my brakes feel spongy".
A_THING_FAILING_WITH_ITS_OWNER = re.compile(
    r"\b(?:my|our|the)\s+(?:[a-z']+\s+)?(?:brakes?|bike|car|boiler|shower|tap|toilet|washing "
    r"machine|dishwasher|fridge|freezer|oven|hob|kettle|hoover|vacuum|computer|laptop|phone|"
    r"heating|radiator|radiators|drain|drains|sink|door|window|lock|roof|gutter|gutters|tyre|"
    r"tyres|engine|gears)\b")

# A person, a bond or a life is not a thing that stopped working: "my marriage is broken" is not
# answered by "what have you tried on it so far", which is what a fridge gets.
A_PERSON_OR_A_BOND = re.compile(
    r"\b(?:marriage|relationship|friendship|husband|wife|partner|boyfriend|girlfriend|ex|mum|mom|"
    r"mother|dad|father|son|daughter|child|children|kids?|family|friends?|mate|boss|colleague|"
    r"job|career|business|life|trust|heart)\b")

# A day with something on it: the person has a plan and is telling the bot about it.
A_DAY_WITH_SOMETHING_ON = re.compile(
    r"\b(?:coming over|coming round|coming to stay|visiting|arriving|staying|we're having|"
    r"were having|im having|i'm having|we're hosting|hosting|party|barbecue|bbq|bday|birthday|"
    r"wedding|christening|funeral|dinner party|roast|big shop|moving house|moving in|"
    r"interview|first day|appointment|exam|driving test)\b")
A_DAY_NAMED = re.compile(
    r"\b(?:today|tomorrow|tonight|this weekend|next week|next month|saturday|sunday|monday|"
    r"tuesday|wednesday|thursday|friday|january|february|march|april|may|june|july|august|"
    r"september|october|november|december)\b")

# They cannot choose, and say so.
A_DECISION_STUCK = re.compile(
    r"\b(?:i (?:dont|don't|do not) know|dno|dunno|no idea)\b[^.?!]{0,24}?"
    r"\b(?:where|what|which|who|whether|if) (?:to|i)\b|"
    r"\b(?:cant|cannot|can't) (?:decide|choose|make up my mind)\b|"
    r"\b(?:torn|stuck) between\b")

# A week with too much in it. "lots on this week" and "i never have time to cook" are not asks,
# and the receipt does not help: the useful thing is to find the one part that is taking the time.
A_LOAD = re.compile(
    r"\b(?:lots on|a lot on|so much on|too much on|everything on at once|no time to|never have "
    r"time|havent got time|haven't got time|run off my feet|rushed off my feet|flat out|"
    r"busy week|mad week|hectic|no minute|not enough hours)\b")

# A worry said with a hedge, where the hedging is the whole point: "i think my ex wants to leave me
# alone", "i dont think i did well". The bot cannot settle it and should not pretend to.
A_HEDGED_READ = re.compile(
    r"\b(?:i think|i feel like|i get the feeling|i suspect)\b[^.?!]{0,40}|"
    r"\bi (?:dont|don't|do not) think i\b")

# Work they cannot get on with, in the words people use for it.
A_WORK_STUCK = re.compile(
    r"\b(?:dno|dunno|dont know|don't know|stuck|fed up|sick of|had enough|had it up to here|"
    r"cant stand|can't stand|dreading)\b[^.?!]{0,32}"
    r"\b(?:job|work|shift|shifts|boss|manager|office|colleagues?|interview|payday|rota)\b|"
    r"\b(?:job|work|shift|shifts|boss|manager|office|interview)\b[^.?!]{0,24}"
    r"\b(?:dno|dunno|dont know|don't know|stuck|fed up|sick of|had enough|dreading|driving me)\b")

# A bill they owe, a payment with no "my" in front of it, and a price somebody has quoted them:
# "i owe 400 on my electric", "mortgage is 900", "the garage wants 400 quid for a service".
A_OWED = re.compile(r"\bi (?:owe|still owe)\b[^.?!]{0,24}?(?:\u00a3|\$)?\d[\d,]*")
A_PAYMENT_NAMED = re.compile(
    r"\b(?:mortgage|rent|council tax|electric|electricity|gas|water|broadband|phone bill)\b"
    r"\s*(?:is|was|are|comes to|=)\s*(?:about|around|roughly|only|just)?\s*(?:\u00a3|\$)?\d")
A_QUOTED_PRICE = re.compile(
    r"\b(?:wants|wanting|quoted|has quoted|said|says|asking|charging|want)\b[^.?!]{0,18}?"
    r"(?:\u00a3|\$)?\d[\d,]*\s*(?:quid|pounds|bucks|euro|euros)?\b[^.?!]{0,20}?"
    r"\b(?:quid|pounds|bucks|for the|for a|to do|to fit|to fix)\b")

THE_OWED = (
    "Is that what is overdue, or the bill itself?",
    "Is that the whole of it, or the first of it?",
    "What happens if it waits until next month?",
)
THE_QUOTED_PRICE = (
    "Is that in writing, and does it include the parts?",
    "Would a second quote be easy to get?",
    "Is that a firm quote or a guess they could add to?",
)

# Somebody else said or did something, and the person is telling the bot about it. What helps is
# the question a friend asks next, not a receipt: "his mates laughed at him", "she calld me
# yesterday". Only the past is read here, so "she says all her mates have had it done" and "she
# doesnt like fuss" keep their reply.
A_PERSON_DID = re.compile(
    r"\b(?:he|she|they|him|her|them|his|hers|their)\b[^.?!]{0,24}?"
    r"\b(?:said|told|texted|calld|called|rang|phoned|replied|laughed|shouted|yelled|ignored|"
    r"asked|sent|wrote|came|went|left|refused|agreed|apologised|turned up|walked|stormed|"
    r"didnt|wouldnt|hasnt|hadnt|couldnt)\b")

# "What was it about?" was the first line here and a reader was right to strike it: "she left the
# shifts off the rota again" says what it was about, so the question reads as though nobody had
# listened. These three fit any line about what somebody did.
THE_PERSON_DID = (
    "And how did that leave you?",
    "What did you say back?",
    "Has it been like this a while, or is it new?",
)

# Two things weighed against each other out loud: "the flat i saw is smaller but it is closer to
# work". Nothing to look up - the person has both halves already and needs one question to decide.
A_COMPARISON = re.compile(
    r"\b(?:is|was|seems|looks|feels|its|it's)\s+(?:much\s+)?(?:more|less|better|worse|bigger|smaller|"
    r"cheaper|dearer|closer|further|farther|easier|harder|nicer|newer|older|quicker|slower)\b"
    r"[^.?!]{0,40}?\b(?:but|though|although|whereas)\b")

THE_COMPARISON = (
    "Which of the two would you notice more in a year?",
    "So which way are you leaning?",
    "What would make it an easy choice?",
)

# A day greeted with a sigh: "monday again". Not a question about the calendar, so nothing to look
# up; the useful thing is to ask what is actually waiting.
A_DAY_SIGHED = re.compile(
    r"^(?:well,?\s*)?(?:its |it's |and )?(?:monday|tuesday|wednesday|thursday|friday|saturday|"
    r"sunday)\b[^.?!]{0,12}\bagain\b|"
    r"\b(?:back to work|another week|is it friday yet|hump day|long week ahead|"
    r"weekend is over|back to reality)\b")

THE_DAY_SIGHED = (
    "What is on today that you are not looking forward to?",
    "Is it the day, or what is waiting on the other side of it?",
    "What would make today easier?",
)
THE_LOAD = (
    "What is the bit of it that is taking the time?",
    "Which of it could come off the list?",
    "What is the one thing you would drop if you could?",
)
# A hedged read of a person is not a hedged read of a thing. "i think my ex wants to leave me alone"
# wants to know what has been said or done; "i think its the pump" is somebody telling you their
# diagnosis, and "what has actually been said or done so far?" asks them about a conversation that
# never happened. The person-shaped question is kept for the person-shaped lines only.
THE_HEDGED_READ = (
    "What has made you think that?",
    "What would you do about it if you were sure?",
)
THE_HEDGED_READ_OF_A_PERSON = THE_HEDGED_READ + (
    "And what has actually been said or done so far?",
)
THE_WORK_STUCK = (
    "Is it the work itself, the people, or what it pays?",
    "What would have to change for it to be bearable?",
    "How long has it been like this?",
)

THE_FIGURE_ALONE = (
    "I've got that figure. Is it what you have to spend, or what it is going to cost?",
    "Noted - and is that on its own, or is there more going out on top of it?",
    "Got that down. What is it for: the thing itself, or everything around it?",
)
THE_FIGURE_THEIRS = {
    "rent": (
        "Is that with the bills in it, or on top of them?",
        "And is that the whole of it, or is there service charge and council tax as well?",
    ),
    "mortgage": (
        "Is that the fixed rate, and how long is left on it?",
        "Is that on its own, or with the insurance and the rest?",
    ),
    "pay": (
        "Is that before tax or what lands in your account?",
        "And is that for the hours you want, or more than you want?",
    ),
    "budget": (
        "What does that have to cover?",
        "What is the one thing in it you would not cut?",
    ),
    "savings": (
        "Is that everything you have put by, or is there more elsewhere?",
        "What are you keeping it for?",
    ),
    "bills": (
        "Which of them is the one that has gone up?",
        "Is that every month, or is it a bill that landed all at once?",
    ),
    "loan": (
        "How long is left on it, and is the rate fixed?",
        "Is that the payment or what is still owed?",
    ),
}
THE_FIGURE_THEIRS_DEFAULT = (
    "Is that on its own, or does it cover the rest as well?",
    "And does that go up at any point, or is it fixed?",
)
THE_BODY = (
    "How long has it been like that, and what makes it worse?",
    "Does anything ease it - rest, heat, or a painkiller?",
    "And is it there all the time, or does it come and go?",
)
THE_THING_FAILING = (
    "What have you tried on it so far?",
    "How long has it been doing that?",
    "Is it doing it all the time, or only now and then?",
)
THE_DAY_WITH_SOMETHING_ON = (
    "How many are you having?",
    "What has to be ready before then?",
    "What is the part you are least sure about?",
)
# A pair the line itself named - "torn between", "the two", "either", "one or the other" - can be
# asked about as a pair. A line that names no options at all cannot: "i dont know where to go" was
# answered "What are the two you are weighing up?" to somebody who has not got two, which asks them
# to supply the premise as well as the answer (a reader's blocker on this PR).
A_PAIR_NAMED = re.compile(
    r"\b(?:torn\s+between|between|the\s+two|both|either|one\s+or\s+the\s+other|"
    r"which\s+one|this\s+or\s+that)\b")
THE_DECISION_PAIR = (
    "What are the two you are weighing up, and what does each one cost you?",
    "Which of the two would you pick if nobody else had an opinion?",
)
THE_DECISION_STUCK = (
    "What is the thing that makes it hard to choose?",
    "Which way would you go if nobody else had an opinion?",
    "What would you need to know first, to pick one?",
)


def reads_as_a_receipt(reply):
    """True only for the composer's own acknowledgements."""
    return bool(reply and A_RECEIPT.search(reply))


def turned(respond):
    """`respond`, with a receipt replaced by a question about the thing the person just said."""
    def reply(text, memory):
        said = respond(text, memory)
        return answer_for(text, memory, said) or said
    return reply


def _money_kind(clean):
    match = A_FIGURE_THEIRS.search(clean)
    if not match:
        return None
    noun = match.group(1)
    if noun in ("pay", "wage", "wages", "income", "salary"):
        return "pay"
    return noun if noun in THE_FIGURE_THEIRS else "default"


def answer_for(text, memory=None, reply=None):
    """One short question about the thing they just said, or None.

    Called with the reply the composer chose: the whole point is that no reader wanted the turn.
    """
    if not reads_as_a_receipt(reply):
        return None
    memory = memory or {}
    clean = str((memory.get("understood") or {}).get("clean") or text or "").lower()
    clean = " ".join(clean.replace("\u2019", "'").split())
    if not clean or len(clean.split()) > 18:
        return None
    if QUESTION.match(clean) or (text or "").strip().endswith("?"):
        return None
    if A_SMALL_LINE.match(clean):
        return None
    if A_OWED.search(clean):
        return pick(list(THE_OWED), memory, clean)
    kind = _money_kind(clean)
    if not kind and A_PAYMENT_NAMED.search(clean):
        kind = _money_kind(clean + " my " + clean.split(" is ")[0])
        kind = kind or "default"
    if kind:
        pool = THE_FIGURE_THEIRS.get(kind) or THE_FIGURE_THEIRS_DEFAULT
        return pick(list(pool), memory, clean)
    if A_FIGURE_ALONE.match(clean):
        return pick(list(THE_FIGURE_ALONE), memory, clean)
    if A_WORK_STUCK.search(clean) and not A_PERSON_OR_A_BOND.search(clean.replace("job", "")
                                                                    .replace("work", "")):
        return pick(list(THE_WORK_STUCK), memory, clean)
    if A_QUOTED_PRICE.search(clean):
        return pick(list(THE_QUOTED_PRICE), memory, clean)
    if A_COMPARISON.search(clean):
        return pick(list(THE_COMPARISON), memory, clean)
    if A_PERSON_DID.search(clean) and not A_PERSON_OR_A_BOND.search(clean):
        return pick(list(THE_PERSON_DID), memory, clean)
    if A_DAY_SIGHED.search(clean):
        return pick(list(THE_DAY_SIGHED), memory, clean)
    if A_LOAD.search(clean):
        return pick(list(THE_LOAD), memory, clean)
    if A_HEDGED_READ.search(clean):
        pool = THE_HEDGED_READ_OF_A_PERSON if A_PERSON_OR_A_BOND.search(clean) \
            else THE_HEDGED_READ
        return pick(list(pool), memory, clean)
    if A_DECISION_STUCK.search(clean):
        # The pair is asked about only where the line named one.
        pool = THE_DECISION_PAIR + THE_DECISION_STUCK if A_PAIR_NAMED.search(clean) \
            else THE_DECISION_STUCK
        return pick(list(pool), memory, clean)
    if A_BODY_PART.search(clean) and A_BODY_QUALIFIER.search(clean):
        return pick(list(THE_BODY), memory, clean)
    if (A_THING_FAILING.search(clean) and not A_PERSON_OR_A_BOND.search(clean)
            and (A_THING_FAILING_WITH_ITS_OWNER.search(clean) or len(clean.split()) <= 8)):
        return pick(list(THE_THING_FAILING), memory, clean)
    if A_DAY_WITH_SOMETHING_ON.search(clean) and A_DAY_NAMED.search(clean):
        return pick(list(THE_DAY_WITH_SOMETHING_ON), memory, clean)
    return None
