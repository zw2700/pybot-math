"""The seed's fallback: it only answers when no other module does."""
import re

from ..compose import breakup
from ..compose import fallback
from ..compose import findout, gap
from ..compose import moving
from ..compose import quantity
from ..compose import no_page
from ..compose import the_course_of_it
from ..compose import checking
from ..compose import goodnews
from ..compose import griefplea
from ..compose import hands
from ..compose import how_it_went
from ..compose import liveask
from ..compose import missing_half
from ..compose import onscreen
from ..compose import own_facts, plans
from ..compose import stretches
from ..compose import safety_doubt
from ..compose import only_they_know
from ..compose import rule
from ..compose import their_day
from ..compose import their_life
from ..compose import taste
from ..compose import the_turn_after
from ..compose import find_a_place
from ..compose import onmybehalf
from ..compose import a_document_lives_with_an_office
from ..compose import a_place_nobody_can_see
from ..memory import ack, detail, matters, obstacle, repeat, too_late
from ..compose import pleased
from ..compose import rotten_luck
from ..compose import said_about_me
from ..compose import nottheirbest
from ..compose import no_eyes
from ..compose import who_to_see
from ..compose import remark
from ..compose import setting_off
from ..memory import ack
from ..memory import back_again
from ..memory import their_feeling

PRIORITY = -1000

# --- a first line that points back at a chat that has not happened ---------------------------
#
# The opening line of a chat sometimes points at something already said: "you told me to wait",
# "you said it was fine", "back to what we were saying", "that thing i told you about". There is
# no earlier turn, so there is nothing for the bot to agree with, and the pools that answer advice
# somebody gave or a day that has happened read these as though it had: "you told me to wait" came
# back as "Sounds like good advice. What's stopping you?", "you said it was fine" as "Sounds
# alright. Anything good in it?" - the bot joining in with a conversation it was not in. Saying
# there is nothing before the line and asking for the thing is the only true answer, and it still
# moves the chat on.
A_REFERS_BACK = re.compile(
    # the bot's own words, claimed back at the person: "you told me to wait", "you said it was
    # fine". Only the past tense - "can i trust what you say" and "how do you say thank you in
    # welsh" are about saying in general, not about a turn that happened.
    r"\b(?:you|u|yous)\s+(?:said|told me|mentioned|suggested|advised|recommended|agreed|"
    r"promised|told me to)\b"
    # the chat itself, named as though it were already under way. The going-back shape has to
    # open the line, so "should i take my coat back to the shop" and "i'll let you get back to
    # it" keep their own answers.
    r"|^(?:(?:o+|oh|and|so|ok|okay|right|now|but|well|anyway|erm|um)\s+)*"
    r"(?:back|going back|return|coming back)\s+to\s+(?:what|that|it|this|where|our|the)\b"
    r"|^(?:(?:o+|oh|and|so|ok|okay|right|now|but|well|anyway|erm|um)\s+)*"
    r"(?:what|which)\s+(?:was|were)\s+we\b"
    r"|\bwhat we (?:were|was) (?:saying|talking about|on about)\b"
    r"|\b(?:the )?same (?:as )?(?:before|last time)\b"
    r"|\bthat thing i (?:told|mentioned|said to|asked) you\b"
    r"|\bas (?:we|you) (?:said|were saying|agreed|discussed)\b"
    r"|\bas i (?:said|mentioned|told you)\b")

NOTHING_BEFORE_IT = (
    "There's nothing before this line for me to go on - say what it was about and I'll pick it up.",
    "I haven't said anything yet, so give me the thing itself: what are we going back to?",
    "Nothing on my side yet - tell me what it was and I'll take it from there.",
    "That's the first thing you've said to me, so I'll need it in full: what was it about?",
)


def _a_line_pointing_back_at_nothing(clean, memory):
    """The pool for an opening line that points at an earlier turn, or None.

    Only when the chat has no turns: after one turn there is something to point at, and every
    reading that answers a real callback keeps the line.
    """
    if not isinstance(memory, dict):
        return None
    if [turn for turn in (memory.get("turns") or []) if isinstance(turn, dict)]:
        return None
    if not A_REFERS_BACK.search(clean or ""):
        return None
    return fallback._choose(NOTHING_BEFORE_IT, memory, clean)


def respond(text, memory):
    # A "still" line - "still cold" after "my shower is cold", "it still clicks" after "my car
    # wont start" - is the thing the chat is on, said again, and the store answers it from that
    # thing. This module is only asked for the lines nothing else would answer, and this module
    # is the last resort that answers them: main's short-line pools read the one word the line
    # carries ("still cold" is the weather) and take the turn before the store's reading gets
    # there, which replaces a good answer with a nod. The reading is asked first here, exactly as
    # the presence pools are stood down for it in `bot/modules/chat.py`, so a "still" line that
    # the store can carry never reaches the pools below (`bot/memory/tried.py`).
    from ..memory import tried as not_moved
    going_on = not_moved.reply_for(text, memory)
    if going_on:
        return going_on
    # A bare "do i need to see anyone" is answered by the someone the answer above already named:
    # after the dog-and-chocolate answer, which said "Ring your vet with the dog's weight ... don't
    # wait for symptoms", the line was met with "That's beyond what I know well, sorry" - the
    # don't-know line, over an answer the bot had just given (bot/compose/who_to_see.py).
    who = who_to_see.reply_for(text, memory)
    if who:
        return who
    # A trouble the chat already had, said to be back ("i have a headache" then "its back", "how
    # do i get rid of slugs" then "the slugs are back"). Nothing above this module claims the
    # line, and the two replies it had were the nod that fits any message and an echo of the
    # person's own words - while the thing coming back says the advice did not hold, which is the
    # one thing worth answering (bot/memory/back_again.py).
    came_back = back_again.reply_for(text, memory)
    if came_back:
        return came_back
    # How somebody else in the chat is finding a thing the chat has named: "my son is 7" / "hes
    # just started school" / "he hates it". Every feeling reader in the bot is about the person
    # typing, so a third person's report got the note that fits any message
    # (bot/memory/their_feeling.py).
    about_them = their_feeling.reply_for(text, memory)
    if about_them:
        return about_them
    # The opening line of a chat pointing back at a turn that never happened (see A_REFERS_BACK).
    # There is nothing to agree with yet, and every pool under this module answers as though the
    # conversation were under way, so the honest line for the first turn is taken here.
    back_at_nothing = _a_line_pointing_back_at_nothing(
        " ".join(str(text or "").lower().split()), memory)
    if back_at_nothing:
        return back_at_nothing
    # The same shape without money: the answer named a rule with a unit ("six to eight glasses a
    # day", "seven to nine hours") and this line is the person's own figure, often with no unit
    # because the answer just used one. "Got it - you drink about 3" tells them nothing about the
    # three; where the figure sits against the rule is the reply
    # (bot/compose/quantity.py, `the_figure_against_the_answer`).
    against = quantity.the_figure_against_the_answer(text, memory)
    if against:
        return against
    # A line that narrows the thing the answer just gave ("its on the bedroom ones mainly") is
    # answered with that answer's one step, with the detail named in front, instead of the
    # composer's echo of the person's own words. It is asked here, before the composer, because
    # this module only ever sees the lines nothing else would answer: the detail of an answer is
    # one of them, and nothing else is taken from a module that can answer for itself.
    # A line judging the answer just given as doable ("ok that sounds doable") is not a detail of
    # it: detail.py reads any short line with a copula in it as one, and says the judgement back as
    # if it were a thing ("The same goes for the sounds doable: ..."). It is asked here, before
    # that reading, because the person is not narrowing the job - they have decided to do it, and
    # the reply a friend gives is to say go on. It says nothing unless there was advice above it.
    accepted = fallback.a_doable(text, memory)
    if accepted:
        return accepted
    # A verdict on the news takes no continuation. "thats a joke" after "my laptop broke" was
    # carried into the laptop answer with "Same for a joke" in front, and "what a hassle" into
    # "Nothing separate for a hassle - it is the same advice": the verdict has no subject of its
    # own, so the detail of the last answer is not what it is about. The composer's own pool is
    # asked for the line instead (bot/compose/fallback.py, `_verdict_pool`).
    verdict = (fallback.reads_as_a_verdict(text, memory)
               and not fallback.a_verdict_stands_down(memory))
    # A verdict is a comment with no subject of its own, so the detail of the last answer is not
    # what it is about - and that holds where the verdict stands down too. "my mum is in hospital"
    # then "thats a pain" was answered "Same answer for a pain: Take in their glasses.": the heavy
    # news stood the verdict pool down, the carry-over underneath it did not stand down with it,
    # and the sympathy pool never got the turn. Whether the verdict pool or the sympathy pool
    # answers, the detail stays where it is.
    a_comment = fallback.reads_as_a_verdict(text, memory)
    carried = None if a_comment else detail.answer_for(text, memory)
    if carried:
        return carried
    # A stated dislike of the thing the last answer leaned on ("i hate exercise" after the plan
    # for losing weight) is answered with the step that does not need it, instead of the
    # composer's echo of the person's own words.
    objected = None if a_comment else obstacle.answer_for(text, memory)
    if objected:
        return objected
    # A report about the thing the last answer was about ("it drops to zero every few days" after
    # the boiler answer) is answered with the sentence of that answer which speaks to it, instead
    # of the nod that fits any message. Asked before the composer because the nod is the composer's
    # last resort, and a nod about the boiler leaves the next line ("is that dangerous") with no
    # subject at all (`detail.a_report_about_the_thing`).
    # The answer to a question the bot has just asked about a noise or a smell - "it came from the
    # loft", "like burning", "under the sink" - is the other half of that exchange, and there is
    # no way to answer it here: the report rule below gives the sentence of the last answer that
    # speaks to the line, which is the question that was just asked. Read before it, and only
    # where the turn before was one of those questions, so no other line can reach it.
    described = no_eyes.what_they_described(text, memory)
    if described:
        return fallback._choose(described, memory, text) or ""
    reported = detail.a_report_about_the_thing(text, memory)
    if reported:
        return reported
    corrected = matters.a_corrected_age(text, memory)
    if corrected:
        # A correction of one of the ages a group of children was given: the composer hands the
        # line back ("Got it - ones 7.") while the store still says four and six, so the bot says
        # the correction landed and then answers "what ages are they" with the old ages.
        return corrected
    # A move is news, but never good news on its own: "im moving out next month" was answered
    # "That's lovely news - and something to look forward to", and people move out after a breakup
    # or an eviction at least as often as into their first flat. The pool here asks about it
    # instead (`bot/compose/moving.py`), and stands aside for a move said as a glad thing.
    off_to = None if a_comment else moving.reply_for(text, memory)
    if off_to:
        return off_to
    # A stated like or dislike of a thing ("i hate mondays", "i love the rain") is a stance to
    # answer, not a fact to file: the composer said it back as "Noted: you hate mondays.", and
    # the same line said with "cant stand" or "dreading" reached the listening pool. The thing is
    # what to ask about, so `bot/compose/taste.py` answers it here - and only here, where nothing
    # else wanted the line. It comes after `matters` because every line it takes is one nothing
    # else wanted, and a corrected age is a fact the store has to keep. It is asked before the
    # composer's one passage through the pools because the line it takes is a receipt or a hedge,
    # and the reading is a stance about a thing rather than a reading of any answer.
    tasted = taste.reply_for(text, memory)
    if tasted:
        return tasted
    # "make it firm but polite" on the turn after a draft was handed over is an edit of words the
    # bot itself printed, not a fact about the world. Every pool the composer has answered it with
    # a shrug - "a quick search online will get you a solid answer", and once the drafting pool's
    # own sample message, about a rota, said firmer - because the line names no subject for any of
    # them. The draft is in the last reply, in quotes, and the tone is the only thing to change
    # (bot/compose/tone_again.py, which stands down unless the line names a tone and nothing else
    # and the bot handed a draft over within the last two turns).
    from ..compose.tone_again import retone
    retoned = retone(memory, text)
    if retoned:
        return retoned
    # The composer's line for this turn is asked once, after the correction above has been written
    # to the store, and every reading below that only replaces a receipt, a hedge or the floor
    # reads that same reply: asking it twice is two passages through the pools for one turn.
    # A bare doubt on top of a safety answer ("is that bad" over the breathing card, the abuse
    # card, the crisis card) is the person checking the thing is as serious as it sounded, and the
    # continuations below are written for lines inside an emergency: it was answered with the care
    # pool of a symptom ("keep an eye on it and tell me if anything changes" over "i hit my wife")
    # and with somebody else's crisis ("keep someone with you tonight" over "my husband hit me").
    # Asked before the composer, because the composer's answer here is the fault.
    serious = safety_doubt.reply_for(text, memory)
    if serious:
        return serious
    reply = fallback.reply_for(text, memory)
    # A thing in the room - a noise, a smell, a light that flashes, half the lights going out -
    # was answered with a placeholder ("Got it. Is there anything you'd like a hand with?",
    # "Thanks for telling me - I'm here if you want to dig into any of that"), which fits any
    # message and leaves the person with a thing in front of them and nothing said about it. The
    # pool says what a thing in that state usually is and where the count or the code is read
    # (bot/compose/no_eyes.py). Only a placeholder is replaced, so no real answer is touched.
    if not a_comment:
        in_the_room = no_eyes.a_thing_in_the_room_over_a_placeholder(text, reply)
        if in_the_room:
            return fallback._choose(in_the_room, memory, text) or ""
        # A recording they are offering, or an address or a number handed over, is a thing the
        # bot can read and nothing it can act on. The receipt ("Got it. Is there anything you'd
        # like a hand with?") reads as though it had arrived, and the search hedge answered "its
        # about 2 mins, can you listen" with a pointer to a search engine.
        if no_eyes._is_a_placeholder(reply) or fallback.is_a_hedge(reply):
            for pool in (no_eyes.a_contact_they_handed_over(text),
                         no_eyes.a_recording_they_offer(text)):
                if pool:
                    return fallback._choose(pool, memory, text) or ""
    # A thing they have, said as a plain fact ("ive got a spare room", "weve got a greenhouse")
    # is not a day that happened. The composer's small-day pool reads the possessive "got" as a
    # past doing and cheers at it - "How was it, overall?", "Nice one. How did the rest of it
    # go?" - and the store's receipt ("Noted: you've got a spare room.") names the thing and
    # asks nothing. Only such a line is replaced here, so a reply the composer has of its own
    # stands, and the replacement says what is true of that kind of thing before it asks
    # (bot/compose/remark.py, `a_thing_of_theirs_reply_for`).
    if reply and (fallback._in_a_pool(reply, (fallback.A_SMALL_DAY,))
                  or ack.reads_as_a_receipt(reply)):
        of_mine = remark.a_thing_of_theirs_reply_for(text, text.split(), memory)
        if of_mine:
            return of_mine
    # Somebody close has handed the person a verdict about themselves - "my mum says im not trying
    # hard enough", "my sister says im a cow", "my boss says im too slow" - and the store files it
    # and hands their own words back ("Noted: your mum says you're not trying hard enough"), or the
    # composer asks what they like most about a cow. Those lines are about being spoken to that
    # way, so the reply says the sting is real and asks the one thing that opens it up. Only a line
    # that claims nothing is replaced, so an answer of the composer's own keeps the turn
    # (bot/compose/said_about_me.py).
    judged_line = said_about_me.reads_as_reported_judgement(text)
    nothing_yet = (not reply or fallback._nothing_to_stand_behind(reply)
                   # The floor can also answer somebody else's words as if they were the person's
                   # own judgement of themselves - "my aunt says im a disappointment to the family"
                   # got "That's a heavy way to feel about yourself" - which argues with the wrong
                   # person about a judgement they did not make.
                   or (judged_line and said_about_me.speaks_to_a_self_judgement(reply)))
    if not a_comment and nothing_yet:
        judged = said_about_me.answer_for(text, memory) or said_about_me.answer_followup(
            text, memory)
        if judged:
            return judged
    # A break-up is not a broken bone. "broke up" sits next to "broke" in the words that say a
    # body is hurt, so a thread that had said it read as an injured patient and the ask after a
    # rough patch ("is she going to be ok") was answered with the pool that names whoever is
    # treating them. Only a reply from those pools is replaced, and only where taking the
    # break-up out of the thread leaves nothing medical behind (bot/compose/breakup.py).
    not_a_body = breakup.answer_for(text, reply, memory)
    if not_a_body:
        return not_a_body
    # A plea for a hand inside a bereavement ("i dont know what to do" the turn after "my mum
    # died last month") is not a line to search for, and the composer had only the search hedge
    # and the nod for it. Only those two are replaced, so a reading with something of its own
    # keeps the turn (bot/compose/griefplea.py).
    keeping_going = griefplea.reply_for(text, reply, memory)
    if keeping_going:
        return keeping_going
    # Nothing has been said yet, so a reply that picks an earlier thread back up is pointing at
    # turns that never happened: "sorry ive been quiet, its been a rough week" as the first line
    # of a chat was answered "No need to say sorry - I'm still here. Where were we?", which
    # sends the person on with a conversation they never started. The pool that line comes from
    # is right late in a chat, so the pointing half goes and the acknowledgement stays.
    reply = first_line_points_back_at_nothing(reply, memory)
    # A win the person puts in a year that has gone - "my book was published in 1998", "he was
    # offered the job in 2015" - is greeted by the congratulations pool as if it had just arrived,
    # which reads as if the bot had not listened. The read is right (it is a happy thing) and the
    # reply is not, so only a congratulations line is replaced: the composer's own line, whatever
    # it is, stands (see `goodnews.reply_for_a_year_ago`).
    years_back = goodnews.reply_for_a_year_ago(text, reply, memory)
    if years_back:
        return years_back
    # A stretch of the day already spent on one thing says how long it has been going on, and the
    # composer had only the stock lines for it ("ive been waiting for the plumber since nine" ->
    # "Got it. Is there anything you'd like a hand with?") or a receipt that asks for the one
    # thing the line had just given ("You've been painting the fence all morning, how long have
    # you been at it?"). The stretch is said back in the person's own time, and the shape of the
    # doing - waiting on somebody, a job of their own, looking after a person - picks the one
    # question that is left (bot/compose/stretches.py). Only a placeholder is replaced.
    stretch = stretches.the_stretch_said_back(text, memory, reply)
    if stretch:
        return stretch
    # The same answer, and the person refuses the move rather than a thing: "theres a mouse in my
    # kitchen" then "i dont want to kill it" was met with the floor ("Got it. Is there anything
    # you'd like a hand with?"), a line that fits any message. A refusal is answered with the
    # sentence of the answer that never needed the move, and only when the composer's reply is a
    # receipt or the floor, so a line it can answer keeps its answer
    # (bot/memory/obstacle.py, `a_move_refused`).
    if not a_comment and reply and fallback._nothing_to_stand_behind(reply):
        refused = obstacle.a_move_refused(text, memory)
        if refused:
            return refused
    # A thing the person cannot use is a limit, not a dislike: "i cant do gyms", "i dont have a
    # car". After an answer that has nothing to hand back without it, the composer has only the
    # nod that fits any message ("Thanks for telling me - I'm here if you want to dig into any of
    # that"), and the person's own limit is what the next reply should be about. Only a reply that
    # answers nothing is replaced: an answer that adapts to what they have not got ("Skip the
    # cheese: a frittata...") is better than any question
    # (bot/memory/obstacle.py, `answer_for_a_thing_they_cannot_use`).
    if reply and (fallback._nothing_to_stand_behind(reply) or fallback._is_a_hedge(reply)):
        cannot_use = obstacle.answer_for_a_thing_they_cannot_use(text, memory)
        if cannot_use:
            return cannot_use
    # A short line that answers the last answer - the detail narrowed to one room, the first step
    # said back as done - is met with the composer's echo of the person's own words, and the part
    # of the answer they have not had yet is still on the screen behind it. It is said back here
    # instead (`the_step_they_have_not_had`).
    rest = the_step_they_have_not_had(text, memory, reply)
    if rest:
        return rest
    # A verdict from somebody with authority - a trade, a clinician, a council - is reported back
    # and the composer hands the person their own words again ("Got it - the plumber said the whole
    # lot needs replacing", "Got it. Is there anything you'd like a hand with?"). What a friend adds
    # is the decision that follows the verdict: a quote in writing and a second price, when to
    # ring back, what the office's own next step is. It is said here instead, and only where the
    # composer had nothing of its own (bot/memory/the_verdict.py) - a receipt, the floor, a hedge, or
    # the small-day pool, which asks a person reporting a plumber's verdict how the afternoon went.
    if reply and (fallback._nothing_to_stand_behind(reply) or fallback._is_a_hedge(reply)
                  or fallback._in_a_pool(reply, (fallback.A_SMALL_DAY,))):
        from ..memory.the_verdict import answer_for as _verdict_for

        verdict_answer = _verdict_for(text, memory)
        if verdict_answer:
            return verdict_answer
    # A follow-up that asks only for a figure ("how long should i leave it", after the answer
    # that said "leave it somewhere warm and airy for at least 24 hours") names no thing, so no
    # entry is reached and the composer reaches for the search hedge - while the figure the person
    # is asking for is in the answer already on their screen. Only a hedge is replaced: when the
    # composer has a line of its own, that line is the reply (see `repeat.the_figure_asked`).
    if reply and fallback._is_a_hedge(reply):
        # The same question, in the same words, asked again after a turn or two of something else:
        # by then the pronouns in it point at whatever was said last, so the store stands down and
        # the hedge is all that is left to say - while the chat already has the answer, word for
        # word the one this line wants. It is handed back, and it is not handed back when anything
        # said since changed the thing the answer was about (see `repeat.the_same_question_again`).
        again_asked = repeat.the_same_question_again(text, memory)
        if again_asked:
            return again_asked
        # A bare "is she going to be ok" about somebody the talk has already said is ill or in
        # hospital has no card behind it, and the hedge ("I don't know enough to answer that
        # honestly. A search should sort you out quickly") is no answer to a person's worry: a
        # search cannot tell anybody whether their mother will be all right. The composer's own
        # line says what is true (nobody can promise it) and who does know (the ward).
        outcome = fallback.an_outcome_asked_about_someone(text, memory)
        if outcome:
            return outcome
        figure = repeat.the_figure_asked(text, memory)
        if figure:
            return figure
        # The other half of that reader: the ask names the thing, and the figure is one the
        # person gave themselves a few turns up ("and how many people" after a roast for 8,
        # "what was my deposit target again" after "i need 20 grand"). Only a hedge is replaced
        # (see `repeat.the_figure_they_gave`).
        figure = repeat.the_figure_they_gave(text, memory)
        if figure:
            return figure
        # A verdict the composer cannot hold - "is it worth fixing", "is the castle worth the
        # money", "are gore tex ones worth it" - wants the number to weigh and where that number
        # comes from, and the hedge gives neither (bot/compose/is_it_worth_it.py). Only a hedge is
        # replaced, and the shapes it reads are the ones where the pointer is certain; a job, a
        # course, a relationship and anything medical keep the composer's own line.
        from ..compose import is_it_worth_it  # noqa: PLC0415 - read here, where the reply is
        worth = is_it_worth_it.is_it_worth_it(text, memory, reply)
        if worth:
            return worth
    # A recall ask the composer has answered with a line that does not carry the figure they
    # asked for: "how much was i putting away" was met with "I can't look up live prices, sorry"
    # and "what was my excess again" with "That is everything I have on that one, so I would only
    # repeat myself" - both while the 400 and the 100 sat in the person's own lines. Only a recall
    # ask ("how much was i", "what was my", "... again"), and only a reply without the figure in
    # it, so a line the composer has answered with the thing itself keeps the turn
    # (bot/memory/repeat.py, `asked_back`).
    back = repeat.asked_back(text, memory)
    if back and not repeat.carries_the_figure(back, reply):
        return back
    # A follow-up that only asks whether the thing is still open to them - "is it too late", "am i
    # too old", "can i still learn" - names nothing of its own, so the composer has nothing but a
    # search hedge for it, while the answer on the screen says in as many words that instructors
    # teach adults who are frightened of the water (bot/memory/too_late.py). Again only a hedge is
    # replaced: a line the composer has an answer for keeps it.
    if reply and fallback._is_a_hedge(reply):
        late = too_late.answer_for(text, memory)
        if late:
            return late
    # A check on a thing in hand, asked after the bot has already named the checks - "what should
    # i check before i pay", "anything i should be careful of" two turns after the price of a
    # second-hand pram - is asking for the sentence the bot itself gave ("A second-hand one is
    # fine if the frame is straight, the brakes hold and the fabric washes"). It reached the
    # search hedge, and the bare form reached the neutral receipt instead, which is not an answer
    # either. The list handed back is the bot's own sentence, so nothing is invented; only a hedge
    # or a receipt is replaced (bot/compose/checking.py, `the_checks_already_named`).
    if reply and (fallback._is_a_hedge(reply)
                  or fallback._in_a_pool(reply, (fallback.NEUTRAL,))):
        checks = checking.the_checks_already_named(text, memory)
        if checks:
            return checks
    # A question about how a thing of theirs went - "how was the wedding", "how did the scan go",
    # "how are the kids", "how is work" - reaches the same hedge, and a search cannot tell anybody
    # how their own week went. The bot was not there; what a friend does is ask and let them tell
    # it (bot/compose/how_it_went.py). Only a hedge is replaced.
    if reply and fallback._is_a_hedge(reply):
        theirs = how_it_went.answer_for(text, memory)
        if theirs:
            return theirs
    # A fact of the person's own life that nobody ever told the bot - "how many brothers do i
    # have", "whats my middle name", "when is my appointment" - reached the search hedge, which is
    # no answer at all: a search engine cannot know how many brothers the person typing has. Only
    # they know, so the reply says the thing back and asks, which is also the move that gives the
    # store the fact (`bot/compose/own_facts.py`). Only a hedge is replaced.
    if reply and fallback._is_a_hedge(reply):
        own = own_facts.answer_for(text, memory)
        if own:
            return own
    # A question about the chats before this one - "can you see my chats with you from before", "is
    # there a list of my chats" - reached the same hedge, and it is the line a search engine is
    # certainly the wrong answer for: it cannot see their chats with this bot either, and the bot
    # is the only thing that knows the answer, which is the shape of the program. Same file, same
    # rule: only a hedge is replaced (`bot/compose/own_facts.py`).
    if reply and fallback._is_a_hedge(reply):
        past = own_facts.about_earlier_chats(text, memory)
        if past:
            return past
    # And whether this chat teaches it anything - "do you learn from these chats", where its twin
    # "do you learn from our chats" was already answered: no page knows how this program works, and
    # the answer belongs in the conversation. Only a hedge is replaced.
    if reply and fallback._is_a_hedge(reply):
        taught = own_facts.learns_from_the_chat(text, memory)
        if taught:
            return taught
    # A plan the person has just told us about, asked about in the next breath - "we fly on the
    # 12th" then "what time do i need to leave" - reaches the same hedge, and a search engine
    # cannot answer a question about somebody's own booking. The plan is theirs and the missing
    # half is in their ticket, so the reply gives the rule of thumb that is worth knowing and asks
    # the one thing that fills the gap (bot/compose/plans.py). Only a hedge is replaced, so a line
    # the composer can answer for itself keeps the turn.
    if reply and fallback._is_a_hedge(reply):
        plan = plans.answer_for(text, memory)
        if plan:
            return plan
    # A question about what time to set off - "what time should i leave", "how early should i get
    # there" - reached the search hedge, and "what time do i need to leave" the live-timetable line
    # about the operator's app. Both name where to look and neither says how the time is worked
    # out, which is the part that can be said: the hour they have to be there, less the journey,
    # less the finding-the-door (bot/compose/setting_off.py). The timetable line is a pointer and
    # not a figure, so it is replaced as well as the hedge; a card with its own figure answers the
    # composer above this reader and keeps the turn.
    if reply and (fallback._is_a_hedge(reply) or fallback._nothing_to_stand_behind(reply)
                  or setting_off.is_a_pointer(reply)):
        off = setting_off.answer_for(text, memory)
        if off:
            return off
    # The answer to that question is the other half of the same exchange: "better than i
    # expected", "not as good as i hoped", "quiet, which is what we wanted". None of those is a
    # question, so the hedge is no use ("A quick search online will get you a solid answer" to
    # somebody's interview) and neither is the nod or the receipt: "worse than last time" was
    # handed straight back as "Got it - worse than last time". The reading is in the same file,
    # and only a line that says nothing back is replaced.
    if reply and (fallback._is_a_hedge(reply) or fallback._nothing_to_stand_behind(reply)):
        gave = (None if (fallback._thread_is_about_the_body(memory)
                         or fallback._the_thread_is_heavy(memory))
                else how_it_went.the_answer_they_gave(text, memory))
        if gave:
            return gave
    # A rule is not the bot's to state - whether something is legal, what a council allows, what
    # a court will do - so those lines reached the search hedge, which tells a person to look up
    # a question no page answers for them. What is true instead is *whose* rule it is and where
    # it is written: the council's own site, the office named on the letter, gov.uk with Citizens
    # Advice. Nothing is stated, and only a hedge is replaced (bot/compose/rule.py).
    if reply and fallback._is_a_hedge(reply):
        owned = rule.answer_for(text, memory)
        if owned:
            return owned
    # The same test, for the lines whose answer is not in this bot at all: "is it on iplayer",
    # "what time is the last train", "anywhere good to eat round there" and "how about moving to
    # spain" all reached the shrug, which tells the person to search without naming what the bot
    # cannot see or where the answer is. The kind of thing is read here
    # (bot/compose/checking.py), and only a hedge is replaced, so no line with an answer of its
    # own changes.
    if reply and fallback._is_a_hedge(reply):
        named = checking.answer_for(text, memory)
        if named:
            return named
    # A pleased remark - "what a lovely day", "what a beautiful morning", "what a relief" - is
    # not a question and there is nothing to look up, but it reaches the same hedge. The bad half
    # of the shape already reads as a complaint; this is the other half, and what it asks for is
    # a few words back and one light question (bot/compose/pleased.py). Only a hedge is replaced.
    if reply and fallback._is_a_hedge(reply):
        glad = pleased.answer_for(text, memory)
        if glad:
            return glad
    # A follow-up that only points at the thread ("will that get better if i keep at it", "will
    # it pass on its own") names nothing of its own, so the composer has the search hedge for it
    # while the thread says exactly whose question it is: a body's is the GP's, a puppy's is the
    # vet's. Only a hedge is replaced, so a card's next step (`the_step_they_have_not_had`) and a
    # line the composer has of its own keep the turn.
    if reply and fallback._is_a_hedge(reply):
        thread = fallback.the_threads_answer(text, memory)
        if thread:
            return thread
    # A question about a thing of their own that only they witnessed - "were the kids ok", "did the
    # doctor ring", "what did the vet say", "did the school get back to you" - has no record behind
    # it, and the composer has nothing for it but a search hedge or a surgery desk ("A pharmacist
    # or your GP can answer that today"); a search engine cannot say how their kids are, and the
    # vet's desk cannot say what the vet told them. `how_it_went` reads the "how was the wedding"
    # half and answers it before this; the reading here is the state of it and the call-back, in
    # bot/compose/their_day.py. Only a reply that is a hedge or one of those who-to-ask lines is
    # replaced, so a line with an answer of its own keeps the turn.
    if reply and (fallback._is_a_hedge(reply) or reply.startswith(their_day.WHO_TO_ASK)):
        asked_back = their_day.pool_for(text, care=fallback._the_thread_is_heavy(memory))
        if asked_back:
            return fallback._choose(asked_back, memory, text)
    # The turn after an honest limit. "Is the library open today" is answered with the hours
    # line, which says where the times are; "and tomorrow" then names no place and asks nothing
    # of its own, so it reached the hedge and told the person to search for what they had just
    # been told where to find. "Can you just check" is the same: the request is put straight back
    # one turn after the bot said it has nothing live. Both are asked here, after every reader
    # that can answer a line of its own (bot/compose/the_turn_after.py), and only a hedge is
    # replaced: the reading claims a line solely where the reply just given was one of the
    # composer's own honest limits, so a bare "and tomorrow" after a card, a joke or a piece of
    # advice changes nothing. An echo is replaced as well as a hedge: "just look it up for me"
    # came back as "Got it - just look it up for you", a machine agreeing to the thing it had just
    # said it cannot do, which is worse than the hedge.
    if reply and (fallback._is_a_hedge(reply) or fallback._nothing_to_stand_behind(reply)):
        after = the_turn_after.answer_for(text, memory)
        if after:
            return after
    # A fact of theirs that a document holds - "whats my rent again", "is my holiday next week",
    # "is my phone covered on holiday", "do i like anchovies" - has no record in this bot and
    # nothing to look up, so the composer has nothing for it but the search hedge: "a quick search
    # online will get you a solid answer" to somebody asking about their own rent. What a friend
    # says is what the bot cannot see, the thing that does have it (a statement, a confirmation
    # email, the person themselves), and one question to carry the talk on
    # (bot/compose/their_day.py, `own_fact_for`). Only a hedge is replaced.
    if reply and fallback._is_a_hedge(reply):
        own = their_day.own_fact_for(text, memory)
        if own:
            return own
    # How to handle a person or a day of their own - "how do i manage my mum", "how do i handle
    # christmas", "how do i sort my life out" - has no page to point at: it depends on the person
    # and on them. The hedge sends them looking for something nobody has written down, so the
    # reply names the parts the ask is really made of and asks which to take first
    # (bot/compose/no_page.py). Only a hedge is replaced, so every how-to with a method behind it
    # (a filter, a boiler, a tax return) and every body or dose question keep their reply.
        parts = no_page.reply_for(text, memory)
        if parts:
            return parts
    # A feeling asked about how long it lasts - "does it get easier", "will i ever feel normal
    # again" - cannot be searched for: nobody can put a date on it. The hedge sends the person to
    # look for a page that would be guessing too, so the reply says honestly that there is no
    # date, gives the shape of it and asks one short question (bot/compose/the_course_of_it.py).
    # Only a hedge is replaced, so a body, a medicine or a thing with a mechanism in it keeps the
    # card that answers it.
    if reply and (fallback._is_a_hedge(reply) or fallback._is_an_ask_which_bit(reply)):
        course = the_course_of_it.reply_for(text, memory)
        if course:
            return course
    # A decision that turns on live information - "should i take a coat tomorrow", "is it open
    # today should i go now" - is answered above with the note about where to look, which says
    # what the bot cannot see and leaves the question itself on the floor. The person asked what
    # to do, so the note keeps its one-tap check and the weighing is handed back in the same reply
    # (bot/compose/liveask.py). Only one of the composer's own live notes is replaced, so a line
    # with an answer of its own, and an ask for the reading alone, are untouched.
    deciding = liveask.answer_for(text, memory, reply)
    if deciding:
        return deciding
    # A comparison of two ages with only one of them ever given ("am i older than my brother",
    # "is my laptop older than my phone") reached the search hedge, and a search cannot know the
    # number that was never said. The half the bot has is said out loud, with what would settle
    # it (`bot/compose/missing_half.py`). Only in place of a hedge, so the store's own comparison
    # of two real ages is untouched.
    if reply and fallback._is_a_hedge(reply):
        one_half = missing_half.the_missing_half(text, memory)
        if one_half:
            return one_half
    # A follow-up about the answer the bot has just given reaches the search hedge while the
    # answer is still on the person's screen: "what should i do about the smell" one line after
    # the answer that says where the smell lives, "should i cut the leaves off" after the powdery
    # mildew answer that says to take the worst off. The sentence of that answer which carries
    # the words they asked with is the reply (`bot/compose/onscreen.py`). Last of the readers
    # that only run on a hedge, so no line with an answer of its own changes.
    if reply and fallback._is_a_hedge(reply):
        # And the step of the answer just given, for a line that asks about it and names nothing
        # of its own ("what do i put in it" after the washing-machine paragraph): it used to reach
        # this hedge over an answer that had just said what to put in (`bot/memory/detail.py`,
        # `the_plain_ask`). Over a hedge only, so a turn that already has an answer keeps it -
        # "i twisted my ankle yesterday" then "ok so whats the best thing to do tonight" has a
        # better one in the composer, "Get it seen today - you'll know either way".
        if not a_comment:
            plain = detail.the_plain_ask(text, memory)
            if plain:
                return plain
        on_screen = onscreen.the_answer_on_screen(text, memory)
        if on_screen:
            return on_screen
    # The same fault one turn further back: the answer this chat gave three turns up, named again
    # by a later line, is not on the screen any more and the composer has no card for the words of
    # the line - "and how do i get some sleep" after the sleep answer reached the search hedge,
    # which sends the person off to look up something the chat already answered. The store has
    # the card, so the sentence of it that carries the words they asked with is said back, as the
    # return it is (bot/memory/asked_about.py). Last of the readers that only run on a hedge.
    if reply and fallback._is_a_hedge(reply):
        from ..memory import asked_about  # noqa: PLC0415 - one reader, imported where it is used

        asked = asked_about.the_answer_this_chat_gave(text, memory)
        if asked:
            return asked
    # A thing of theirs that has been damaged, taken, refused or fallen off is not a day that went
    # well, and the composer's small-day pool congratulates it: "we had a flood" got "Nice one. How
    # did the rest of it go?" and "someone keyed my car" got "Good to hear. What was the best
    # bit?". So does a thin receipt with no question after it ("Rotten luck.", "Got it. Is there
    # anything you'd like a hand with?"). Only one of those is replaced, so a line with an answer
    # of its own keeps the turn (bot/compose/rotten_luck.py).
    if reply:
        not_good = rotten_luck.answer_for(text, memory, reply)
        if not_good:
            return not_good
    # A day denied ("not my best day") or graded low by comparison ("ive had better weeks", "could
    # be better") is a report, not a request: the good-time pool congratulates it ("That sounds like
    # a good time - what was the best of it?") because "best day" is a good word and the pool cannot
    # see the "not", and a graded day has no BAD_STRETCH word in it at all, so the understanding
    # engine read the shape as an ask and the composer reached for the search hedge. Nobody looks up
    # how their own week is going. Only a congratulation, a shrug of an ack or a hedge is replaced,
    # so a line with an answer of its own keeps the turn (bot/compose/nottheirbest.py).
    low_day = nottheirbest.answer_for(text, reply, memory)
    if low_day:
        return low_day
    # A judgement put to the bot ("do you think shes too old for a day out", "was i out of order")
    # or a yes/no about one of their own people ("does my mum like golf", "do they get on at that
    # age") is not a look-up, and the search hedge is the one answer that cannot help: it sends
    # somebody off to read about their own family. Only the composer's own "I cannot answer that"
    # note is replaced, so a line with an answer of its own keeps it
    # (bot/compose/only_they_know.py).
    if reply and reply[:40] in [line[:40] for line in fallback.UNKNOWN]:
        only = only_they_know.answer_for(text, memory)
        if only:
            return only
    # A record is held by one office rather than sold anywhere - "where do i get the deeds",
    # "where can i find the log book for my car", "where can i get a probate record". The reader
    # below answers that shape with a map app and a ring first, which is right for a bike tyre and
    # sends somebody driving for a document that has a single holder. What the bot knows is which
    # office holds which kind of record, and the office's own service is where the copy is ordered,
    # so the reply says that first. Asked before the map-app reader, and over a hedge, that
    # reader's own line, or a lost record the composer reads as a feeling ("we lost the log
    # book" -> "That sounds rough"), so a card that names the office keeps the turn
    # (bot/compose/a_document_lives_with_an_office.py).
    if reply and (fallback._is_a_hedge(reply)
                  or a_document_lives_with_an_office.a_map_app_line(reply)
                  or a_document_lives_with_an_office.a_lost_record(text, reply)):
        held = a_document_lives_with_an_office.answer_for(text, memory, reply)
        if held:
            return held
    # A question about where to get a thing, or somebody to do a job - "where do i get seed from",
    # "is there a launderette near me", "any decent chippy near me" - needs a map, a branch list
    # and today's times, and there is none of that on this side. The composer has
    # the search hedge or, worse, the flat nod for it ("Thanks for telling me - I'm here if you
    # want to dig into any of that"). The true part is small - no map, no list, no opening times -
    # and the move that works is a map app with their own town in it, or two neighbours for a
    # trade (bot/compose/find_a_place.py). Only a hedge or the nod is replaced, and never one that
    # already names the finder or the register: that route is the better answer to hand over to.
    if reply and (fallback._is_a_hedge(reply) or reply in find_a_place.A_NOD):
        here = (None if find_a_place.already_a_route(reply)
                else find_a_place.answer_for(text, memory))
        if here:
            return here
    # A line that hands the bot the errand itself - "search for flights for me", "book the
    # tickets", "send me the recipe", "save this for later", "add milk to my shopping list" - is
    # not small talk, and it was answered with one of the composer's flat readings ("Got it. Is
    # there anything you'd like a hand with?"). Nothing here has hands, a browser, an account or a
    # list that outlives the chat, so the true reply names that in a few words, says what the bot
    # can still do, and leaves the errand where it happens (bot/compose/onmybehalf.py). Only those
    # flat readings are replaced, so a line with an answer of its own never reaches it.
    if reply:
        handed = onmybehalf.answer_for(text, memory, reply)
        if handed:
            return handed

    # A judgement on a place or a thing the bot cannot see ("is benidorm ok with a toddler", "is the
    # old town doable", "is this area safe", "is my bike safe to ride", "is that a good trade")
    # reached the search hedge, which sends a person off to read reviews they could have found
    # themselves. It leads with what it can say - the things that actually decide that kind of thing
    # - and then names where the live detail is. Only a hedge is replaced, and it is asked last, so
    # a card, an entry, `checking`, `only_they_know`, `find_a_place` and the composer's own line all
    # keep the turn (bot/compose/a_place_nobody_can_see.py).
    if reply and fallback._is_a_hedge(reply):
        judged = a_place_nobody_can_see.answer_for(text, memory, reply)
        if judged:
            return judged
    # A last reader of the hedge: a thing the person named, with a kind, and an ask about it that
    # the kind does not decide on its own - a schedule, a cleaning, a figure. What the kind makes
    # true is said, and the exact part is named as the place the rest lives
    # (bot/compose/what_i_do_know.py). Only a hedge is replaced, so a card, an entry and every
    # reader above keep their turn.
    if reply and fallback._is_a_hedge(reply):
        from ..compose import what_i_do_know  # noqa: PLC0415 - read here, where the reply is
        known = what_i_do_know.reply_for(text, memory, reply)
        if known:
            return known

    # A follow-up that asks for no figure at all - "do i need to prick them", "can i still eat
    # it", "and should i cover it" - is still answered by the card on the screen: the sentence of
    # it that says what is safe, or the step it gives first. It is asked here, after every reading
    # of its own above and before the hedge, and only where the live reply is one that answers
    # nothing - a hedge, the note that the answer above was all of it, a receipt, or one of the
    # lines that hand the question back. Where the card has no such part, the part it does know
    # still comes back, with the one thing it never said and the one place that settles it
    # (bot/memory/repeat.py, `the_part_asked` and `what_it_knows`).
    if repeat.answers_nothing(reply):
        part = repeat.the_part_asked(text, memory)
        if part:
            return part
        # Never over an answer that already sent them to 111, A&E or a vet: the step is given and
        # the line after it is asking about everything else.
        if not repeat.the_advice_was_to_get_seen(memory):
            knows = repeat.what_it_knows(text, memory)
            if knows:
                return knows

    # The last thing this bot says to a question nothing answered is the search hedge, or one of
    # the three receipts that are not answers either ("Got it. Is there anything you'd like a hand
    # with?"). STYLE.md's "Not knowing, honestly" asks for the other thing: say what the bot cannot
    # see and name the one place that does know. The kind of gap is read off the ask alone, in
    # bot/compose/findout.py, which holds no fact about the world - only where the answer lives, so
    # it cannot go stale. Only a hedge or a receipt is replaced, and only one that names nothing
    # itself: a hedge that already sends the person to the map app or the council has the reading
    # above already, said shorter (`findout.says_where_to_look`), so a line the composer has an
    # answer of its own for keeps the turn.
    understood = memory.get("understood")
    clean = ((understood.get("clean") if isinstance(understood, dict) else None)
             or " ".join(text.lower().split()))
    # A hedge that names a page still gives way where the ask has a kind of its own: "how long is
    # the wait" was answered with the Wikipedia pointer, and a page is not what was asked about the
    # next hour (`findout.reads_as_busy`).
    thinner = bool(reply) and (fallback._in_a_pool(reply, (fallback.NEUTRAL,))
                               or (fallback._is_a_hedge(reply)
                                   and (findout.reads_as_busy(clean)
                                        or not findout.says_where_to_look(reply))))
    if thinner:
        elsewhere = findout.pool(clean, memory) or findout.more_about_the_journey(clean, memory)
        # A status word spent on a named road or line is an ask even where the reader above wants
        # the thing it is spent on to be one it knows ("delays on the a38"), and the receipt is
        # what it would otherwise get. Asked only on that receipt, so every kind above keeps its
        # turn (`findout.pool_over_a_receipt`).
        if not elsewhere and fallback._in_a_pool(reply, (fallback.NEUTRAL,)):
            elsewhere = findout.pool_over_a_receipt(clean)
        if elsewhere:
            return fallback._choose(elsewhere, memory, clean)
    # Most of the asks nothing answered are not look-ups at all: "do i need to be in for it" is
    # answered by the delivery note in their hand and "what tools will we need" by the instruction
    # sheet in the box. The bot cannot see either, but it does know which one it is, so the reply
    # names the subject back, names the thing that carries the rest, and asks the one question that
    # narrows it (`findout.on_the_thing`). Only a hedge is replaced, and this is asked after every
    # reader that names its own subject, so each of those keeps its turn; it is asked before the
    # `gap` reader below because a carrier is the more particular answer of the two ("do i need to
    # be in for it" is settled by the delivery note, not by what the rules say).
    if reply and fallback._is_a_hedge(reply):
        looked = findout.on_the_thing(text, memory, memory.get("understood"))
        if looked:
            return looked
    # A gap whose answer is in no one place: a quote or a published rate, a verdict on one thing,
    # a fit, a figure about a place, whether it is allowed, how to do a thing. The reader above
    # needs a thing named in the line, so these reached
    # the shrug or a pointer instead - "A quick search online will get you a solid answer", "the
    # Wikipedia page or the official site will have it". What that kind of ask turns on is known
    # even when the number is not, and saying it before the page is the difference between a
    # reply and a signpost (STYLE.md, "Not knowing, honestly"; bot/compose/gap.py). Only a shrug
    # or a pointer is replaced and only where the kind is read, so an answer of the composer's
    # own keeps the turn.
    if reply and (fallback._is_a_hedge(reply) or gap.names_only_a_page(reply)) \
            and not gap.names_the_paper(reply):
        gap_lines = gap.pool(clean)
        if gap_lines:
            return fallback._choose(gap_lines, memory, clean)
    # An ask the bot has no hands for - "set a timer for 20 mins", "play some music", "note that
    # down" - is a job, and a job answered with the stock nod or with the person's own words said
    # back reads as done. What it says instead is the limit in a few words and the half that can
    # happen here (bot/compose/hands.py). A place means a hedge, the nod, or a receipt; a line the
    # composer had something of its own to say about keeps it, and so does the pool for a job in
    # the world unless the half the person asked for is the words.
    # "read my emails for me" is the same fault one pool over: the composer took the imperative
    # for an account of a day and answered "Good to hear. What was the best bit?", which hears a
    # job and asks about an afternoon. So the small-day pleasantry is a place too - the line still
    # has to read as a job, so an account of a day keeps its reply.
    a_place = (fallback._is_a_hedge(reply)
               or fallback._in_a_pool(reply, (fallback.NEUTRAL, fallback.A_SMALL_DAY))
               or ack.reads_as_a_receipt(reply))
    if not a_place and hands.writes_the_words(text):
        a_place = fallback._in_a_pool(reply, (fallback.ACTS_FOR_ME,))
    if a_place:
        hands_reply = hands.reply_for(text, memory)
        if hands_reply:
            return hands_reply
    # A particular of the person's own life - "do i like fish", "what does she do", "how old is
    # he", "who is my friend coming with" - has no page anywhere: the only places it lives are the
    # person in front of the bot and the people around them, so the search hedge sends them
    # looking for something nobody has written down. The honest line says the bot has not met them
    # and asks for the one thing it needs (bot/compose/their_life.py). Only a hedge is replaced, so
    # a card, a thread that remembers, an own record and a safety answer keep their turn.
    if reply and fallback._is_a_hedge(reply):
        own_life = their_life.reply_for(text, memory)
        if own_life:
            return own_life
    return reply


# The arbiter asks this before the never-repeat rule and the specialist fit (README.md,
# "Interface"): the composer says which lines are its own, and the arbiter takes its word. Three
# readings live here, and each has to keep the others:
#
#   - a bare "why" after an answer, where the composer gives the reason out of the answer it gave
#     instead of the knowledge module handing the whole paragraph back, and a report on the advice
#     just given ("its not helping") - `fallback.TAKES_AS_IT_COMES`;
#   - a question about the bot itself, which no entry about the world can answer: "are you
#     connected to the internet" reached the guest-wifi card, "what model do you run" the search
#     hedge, "what cant you help with" the shrug (bot/compose/fallback.py, `reads_as_about_itself`);
#   - a line that only says the money has run out, where the reply is about the tight week and not
#     about saving: the money entry read "skint" and answered how to free up cash over months to
#     somebody asking how to get to Friday (`reads_as_a_tight_week`).
#
# So it is one declaration that says yes to either, never two: a second `TAKES_AS_IT_COMES` in
# this file rebinds the name and the first one silently stops being asked.
# The words a later sentence of an answer uses when it holds a step rather than a sign-off. The
# rest of an answer is only worth saying when there is a step in it: the leftover of "Hope that
# helps. Take care." would otherwise be handed back as the reply.
A_STEP_IN_IT = ("check", "clear", "tr", "us", "put", "add", "set", "switch", "turn", "leav",
                "keep", "ask", "tak", "replace", "restart", "update", "mov", "clean", "fix",
                "buy", "get", "call", "ring", "book", "look", "mak", "run", "wash", "charg",
                "delet", "start", "install", "plug", "test", "measur", "wip", "help", "need",
                "work", "cost", "sav")
# A line that pushes back on the answer ("...though", "but it still does it") is an objection,
# and an objection has its own reading. The rest of the answer is for a line that adds to it.
PUSHING_BACK = re.compile(r"\b(?:though|but|actually|still|to be honest|honestly)\b", re.I)
SIGNING_OFF = ("hope", "good luck", "sorry", "take care", "all the best", "let me know",
               "good question", "that said")
SENTENCE = re.compile(r"(?<=[.!?])\s+")
# A quotation in an answer is a sentence the person can say, and the full stop or question mark
# inside it is not the end of the card's own sentence. Counting the quote marks before a boundary
# says whether it is inside one; a straight apostrophe is only a quote when it stands at the edge
# of a word, so "don't" and "bear's" are not mistaken for one.
QUOTE_MARK = re.compile(r"[\u2018\u2019\u201c\u201d\"]|(?<![A-Za-z])'|'(?![A-Za-z])")


# A reply that takes up the thread again rather than answering anything: these are the phrases
# the composer's own pools use when a chat resumes, and each of them says "the thing we were on
# before this", which the first line of a chat has not got.
_POINTS_BACK = re.compile(
    r"^(?:so[, ]+)?(?:where were we|where did we get to|what were you saying|"
    r"what were we saying|what were we talking about|what was i saying)[?.!]*$"
    r"|^(?:and )?back to (?:it|that|what we were saying|what we were talking about)[.!]*$"
    r"|^(?:as|like) (?:i|we) (?:said|were saying|mentioned)[.!]*$",
    re.I)
# What a friend says instead when the apology or the pause is the whole of the line: the
# acknowledgement stands and the invitation to go on is said fresh, not pointed backwards.
_GO_ON = "Go on - what has been happening?"


def first_line_points_back_at_nothing(reply, memory):
    """The reply, with any "where were we" taken out when nothing has been said before it.

    A chat's first line has no earlier thread: an apology for being quiet ("sorry ive been quiet,
    its been a rough week") is the first thing the person has said, and "Where were we?" asks them
    to resume a conversation that does not exist. Only a reply whose last sentence points back is
    touched, only when the bot has not answered anything yet, and the rest of the reply is kept as
    it is, so a card that answers something keeps its whole answer.
    """
    if not isinstance(reply, str) or not reply.strip():
        return reply
    memory = memory if isinstance(memory, dict) else {}
    said_before = [one for one in (memory.get("turns") or []) if isinstance(one, dict)]
    if any(str(one.get("bot") or "").strip() for one in said_before):
        return reply
    sentences = [one for one in SENTENCE.split(reply.strip()) if one.strip()]
    if not sentences or not _POINTS_BACK.match(sentences[-1].strip()):
        return reply
    kept = " ".join(one for one in sentences[:-1] if one.strip())
    if not kept:
        return _GO_ON
    # A reply that answered something has already said the useful part, so the invitation is only
    # added where the pointing sentence was all the reply had after it.
    return kept if len(kept.split()) > 6 else kept + " " + _GO_ON


def sentences_of(answer):
    """The answer's sentences, with a boundary inside an open quotation left alone.

    A card often quotes the words a person can say ("Say it as a preference and not as a
    rejection, once, warmly: 'I love that you think of me - could we do a coffee and a walk
    instead of a top? I only wear two of them.' Then make it easy for her..."). The question mark
    is inside the quotation, so the card's sentence runs on past it, and splitting there handed
    the person "I only wear two of them.' Then make it easy for her..." - a leftover that opens
    mid-quote, which can never read right.
    """
    out, start = [], 0
    for match in SENTENCE.finditer(answer):
        piece = answer[start:match.start()]
        if len(QUOTE_MARK.findall(piece)) % 2:
            continue  # a full stop inside a quotation the answer has not closed yet
        out.append(piece.strip())
        start = match.end()
    out.append(answer[start:].strip())
    return [one for one in out if one]
# "Switch the printer off and on at the wall, then check the queue": the answer names its own
# first step, and a person who says they have done that step has the rest of the sentence still
# to come. The clause before "then" is the step they say they have done.
THEN_TAIL = re.compile(r"\bthen\b,?\s*", re.I)
# A step reported done opens the door only when it is a step of THIS answer. "ive turned it off and
# on" says the printer instruction back to the printer; "i topped up my phone", over an answer about
# a boiler, is a different job, and the boiler's next step is then handed to somebody who asked
# nothing of it. The line has to share a word with the answer it follows, or be the same on-and-off
# cycle the answer asked for, which is the one step people report in words of their own.
PLAIN = frozenset("""about after again all already also and any are because been before being but
both can could did does doing done dont down each even ever every for from get got had has have
having her here hers him his how into its just know like made make many more most much must my
never not now off on once one only other our out over own said same says she should since some
still such than that the their them then there these they thing things think this those though
through time too took under until very was way were what when where which while who why will with
would yes yet you your youre ive im id ill youve weve theyre isnt dont cant didnt wasnt
havent hasnt wouldnt couldnt shouldnt thats whats lets okay ok min little bit lot thing
stuff""".split())
RESTART = re.compile(r"\b(?:turn\w*|switch\w*|restart\w*|reboot\w*|reset\w*|unplug\w*|"
                     r"plug\w*|power\w*|off)\b")


def _a_step_of_this_answer(text, answer):
    """True when the step they report is one of the answer's own, so its next step is theirs."""
    # Every thing the line names has to be in the answer, not just one of them: "i checked the
    # football scores" shares the word "check" with a boiler answer and is still a different job,
    # while "i deleted some things" is the laptop answer's own step. Five letters, so "deleted" is
    # "delete": the tense and the ending are the same word to a person reading it.
    words = [word for word in re.findall(r"[a-z']+", str(text or "").lower())
             if len(word) > 2 and word not in PLAIN]
    theirs = {word[:5] for word in re.findall(r"[a-z']+", str(answer or "").lower())}
    restarting = bool(RESTART.search(str(text or "").lower())) and bool(
        RESTART.search(str(answer or "").lower()))
    for word in words:
        if word[:5] in theirs or (restarting and RESTART.search(word)):
            continue
        return False
    return bool(words)
# A line that says the first step is already done: "ive turned it off and on", "i did that",
# "i already tried it". The words it shares with the instruction are not the point - the tense
# is - so this is read as a shape rather than by matching the answer's own words.
# The line has to be about the answer, and one of these says so: a detail narrowed to a place or
# a thing ("in the kitchen", "a fan oven", "it was the weather"), or a step reported as done. A
# report about somebody else's reaction ("she got defensive") is neither, and the answer's
# leftover is then not about it - the answer it came from may not even be about their question.
A_DETAIL_OF_IT = re.compile(
    r"\b(?:in|on|at|by|near|under|over|behind|inside|outside|next to)\s+(?:the|a|an|my|our|his|her|their)?\s*[a-z]+"
    r"|\b(?:it|its|it's|they|theyre|they're|he|she|that|this|there)\s*"
    r"(?:'s|s| is| are| was| were| arent| isn't| isnt)\s+(?:a|an|the|not|quite|just|still|only)?\s*[a-z]+"
    # "they only offered a voucher", "he replaced the filter": what somebody did about it
    r"|\b(?:they|he|she|we|you|it)\s+(?:only\s+|just\s+|already\s+|also\s+)?[a-z]+ed\b",
    re.I)
# "my review is next month", "our boiler is a combi": a fact about something they own or owe.
# Kept apart from the shapes above because it is only a detail of the answer when the answer is
# about the thing the line names - see `_answers_the_line`.
A_FACT_OF_THEIRS = re.compile(
    r"\b(?:my|our|his|her|their|the)\s+[a-z]+\s+(?:is|are|was|were)\s+[a-z0-9]+", re.I)
DONE_A_STEP = re.compile(
    r"\b(?:i|ive|i've|i've)\s*(?:have\s+)?(?:already\s+)?(?:[a-z]+ed|done|tried|did)\b"
    r"|\b(?:did|tried|done) (?:that|it|this)(?: already)?\b"
    r"|\balready (?:did|done|tried)\b", re.I)
# A line can carry a detail of the thing and still not be about the answer: "call the plumber on
# monday", after the hot water stopped working, names what they will do and when, and the rest of
# the boiler's card is the answer they already had. A time ahead and a thing to do are what make
# it a plan for later rather than a detail of the fault, so the leftover is not said back.
A_TIME_AHEAD = re.compile(
    r"\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday|tomorrow|tonight|later|soon|"
    r"weekend|next\s+(?:week|month|year|time)|this\s+(?:morning|afternoon|evening|week|month)|"
    r"in\s+the\s+(?:morning|afternoon|evening)|in\s+(?:a|an)\s+(?:bit|while|minute|hour)|"
    r"in\s+a\s+few\s+days|after\s+work|day\s+after\s+tomorrow)\b",
    re.I)
A_DOING_SOON = re.compile(
    r"\b(?:call\w*|ring\w*|phon\w*|get\w*|sort\w*|tak\w*|book\w*|do|doing|fix\w*|go|going|"
    r"see|seeing|bring\w*|order\w*|ask\w*|contact\w*|chas\w*|email\w*|messag\w*|text\w*|"
    r"arrang\w*|hir\w*|report\w*|pop\w*|drop\w*|look\w*)\b", re.I)
# "i called them on monday" is a step reported as done, which is the other shape, so a word in
# the past tense is not a doing-soon.
PAST_TENSE = re.compile(r"ed$", re.I)
# A line that adds a fact about somebody - an allergy, an intolerance, a diet, a food they will
# not eat - is news of the chat, not an answer to the answer, however short it is and however
# much of it looks like a detail of the thing. "one of the kids is allergic to dairy" after the
# pudding list came back with the list's second sentence (rice pudding, bread and butter pudding,
# Eton mess), which is the one thing that child cannot have: the receipt is the whole reply, and
# the leftover stays where it is.
A_NEW_FACT_ABOUT_SOMEONE = re.compile(
    r"\ballerg\w*|\bintoleran\w*|\bcoeliac|\bceliac|\blactose\b"
    r"|\b(?:is|im|i'm|are|we're|were)\s+(?:a\s+)?(?:vegetarian|vegan|pescatarian)\b"
    r"|\b(?:doesnt|does not|dont|do not|wont|will not|never|can'?t|cant)\s+"
    r"(?:eat|drink|have|touch)\b",
    re.I)


def _a_plan_for_later(text):
    """True when the line says what they will do and when, rather than how things are.

    Both halves are needed. A time on its own is a detail ("it started in the garden on
    saturday") and a doing verb on its own is not ahead of them ("check the queue") - it is the
    two together, with the doing not yet in the past, that puts the line in the future: "im
    taking it back tomorrow", "i'll do it at the weekend", "get someone in next week".
    """
    if DONE_A_STEP.search(text):
        return False
    if not A_TIME_AHEAD.search(text):
        return False
    for doing in A_DOING_SOON.finditer(text):
        if not PAST_TENSE.search(doing.group(0)):
            return True
    return False


def _answers_the_line(text, answer, turns=()):
    """True when the line is a detail of that answer rather than news of its own.

    A place or a thing named, a pronoun said about it, or a step reported as done is about the
    answer whatever the answer is. A fact of theirs ("my review is next month") is only about
    the answer when the answer is about the thing it names: "my daughter is allergic to milk"
    came after an answer about nuts, and the leftover of that answer - "check the labels on
    chocolate, muesli, pesto and satay, and anything marked 'may contain nuts'" - was handed back
    as advice about milk, which is a wrong fact about a child's allergy. Nothing in the answer was
    about the daughter or the milk, so the line is news and keeps the composer's own reply.
    """
    if A_DETAIL_OF_IT.search(text) or DONE_A_STEP.search(text):
        return True
    if not A_FACT_OF_THEIRS.search(text):
        return False
    # The words that carry a subject, the way the composer counts them: "not very good with
    # phones" shares "with" with any answer at all, so a plain word set would let every line
    # through. A fact that names something of the answer ("my review is next month", after an
    # answer about the review) is a detail of it.
    named = set(fallback.content_words(text))
    if named & set(fallback.content_words(answer)):
        return True
    # A line that puts the same kind of fact again about a different thing shares its words with
    # the line before, not with the answer, and the leftover is about the first thing: "my son is
    # allergic to nuts" then "my daughter is allergic to milk" handed back "check the labels on
    # chocolate, muesli, pesto and satay, and anything marked 'may contain nuts'", which is a
    # wrong fact about a child's allergy. A fact about something new to the talk keeps the
    # leftover ("my mum is 78 and not very good with phones", after the group-chat answer).
    asked_before = " ".join(str(one.get("user") or "") for one in turns[-1:])
    return not (named & set(fallback.content_words(asked_before)))


def _said_back(text, said):
    """True when the reply is the person's own words back, with no claim added.

    The composer's ack ("Got it - you've turned it off and on") keeps the person's words and
    adds a receipt, so the test is on the person's words: three quarters of what they said is in
    the reply, and at least two of their words are. A reply that says something else shares
    nothing with the line, which is how a real answer is told from a receipt.
    """
    mine = fallback._the_words(text)
    theirs = fallback._the_words(said)
    if len(mine) < 2 or not theirs:
        return False
    # A hedge is not the person's words back, even when it repeats the thing they named: "find
    # me a plumber near me" is answered with "a search for plumber near you, sorted by reviews",
    # which is the words of the ask inside a hand-off and not a receipt for it. Reading it as an
    # echo made the next ask get the second sentence of the hedge before it - a map app for the
    # postcode, said again to somebody asking for a plumber.
    if fallback._is_a_hedge(said):
        return False
    shared = mine & theirs
    return len(shared) >= 2 and len(shared) / len(mine) >= 0.6


def the_step_they_have_not_had(text, memory, said):
    """The part of the last answer the person has not had yet, or "" when there is none.

    "the wifi keeps dropping in the back bedroom" is answered with two sentences, the second of
    which is the branch for one room still dropping; "its fine in the kitchen" then got the
    composer's echo back - "Got it - it's fine in the kitchen" - with the branch still on the
    screen. The person has answered the answer, so the reply is the answer's second sentence, not
    their own words.

    It is asked only of a reply that is an echo: a module that can answer for itself has already
    answered, and a real line from the composer is never replaced. The line has to be short and
    not a question, and the leftover has to hold a step, so a sign-off is not said back. A line
    that says what they will do about it, and when, is a plan for later: "call the plumber on
    monday" has read the answer, so the rest of it is not what they are waiting for.
    """
    said = str(said or "").strip()
    # Two replies stand in for the echo: the composer's ack of the person's own words, and its
    # question about how the day went. "ive turned it off and on", after the printer answer,
    # matched the account-of-the-day pool (#6500) and was congratulated with "Good to hear. What
    # was the best bit?" over an answer whose next step was "then check the queue" - the same
    # turn an echo would have taken, with a warmer receipt in front of it. Only a line that says
    # a step was done opens that second door: an account of a day is still an account of a day.
    an_echo = _said_back(text, said)
    a_step_done = bool(DONE_A_STEP.search(text)) and fallback._a_small_day(text, memory)
    if not said or not (an_echo or a_step_done):
        return ""
    if fallback.is_a_forecast(said):
        # "will that get better if i keep at it" shares "get", "better" and "keep" with the
        # composed line about whose call it is, so the line read as an echo of their words and
        # the answer they had already read was said back. A line that names who can settle the
        # question is not a receipt.
        return ""
    if fallback.is_a_forecast(said):
        # "will that get better if i keep at it" shares "get", "better" and "keep" with the
        # composed line about whose call it is, so the line read as an echo of their words and
        # the answer they had already read was said back. A line that names who can settle the
        # question is not a receipt.
        return ""
    # An echo that asks the person something of its own is not a receipt. "i work nights in a
    # care home" mid-chat was echoed back as "You work nights in a care home — so that is the part
    # behind it. What has been hardest about it?", which leaves them a question to answer; the
    # step from the answer before ("Get the food and the rest in first, and leave the rest till
    # tomorrow") is then said a second time, on the turn they told the bot something new. A
    # receipt is the person's words plus a nod, and a nod never ends in a question mark.
    # It stands aside for the second door: the pool's own reply to a step done is a question
    # ("Good to hear. What was the best bit?"), so the rule that keeps a question out of the
    # receipt would shut the door behind the one line it was opened for.
    if "?" in said and not (a_step_done and not an_echo):
        return ""
    words = re.findall(r"[a-z']+", str(text or "").lower())
    if not words or len(words) > 12 or "?" in str(text or ""):
        return ""
    turns = [one for one in (memory.get("turns") or []) if isinstance(one, dict)]
    answer = str(turns[-1].get("bot") or "").strip() if turns else ""
    if not answer or not _answers_the_line(text, answer, turns):
        return ""
    if _the_answer_again(answer, turns):
        return ""
    if PUSHING_BACK.search(text):
        return ""
    if A_NEW_FACT_ABOUT_SOMEONE.search(text):
        return ""
    if _a_plan_for_later(text):
        return ""
    if fallback.reads_as_a_verdict(text, memory) or fallback.a_verdict_stands_down(memory):
        return ""
    if a_step_done and not an_echo and not _a_step_of_this_answer(text, answer):
        return ""
    sentences = sentences_of(answer)
    # Two ways in, and either may hold the step: everything after the answer's first sentence,
    # and everything after the instruction the person says they have already carried out
    # ("Switch the printer off and on at the wall, then check the queue").
    candidates = []
    # When the door was opened by a step reported done, the only thing they are owed is the step
    # after the one they did. The rest of the answer is not: "my knee hurts when i run" / "ive
    # tried them all" is a person who has read the paragraph, and handing back its second half
    # was the repeat main already learned to avoid.
    if len(sentences) > 1 and not (a_step_done and not an_echo):
        candidates.append(" ".join(sentences[1:3]))
    did_a_step = bool(DONE_A_STEP.search(text))
    for match in THEN_TAIL.finditer(answer):
        if not did_a_step and not _said_back(text, answer[:match.start()]):
            continue
        after = answer[match.end():].strip()
        if after:
            candidates.append(after[0].upper() + after[1:])
        break
    for leftover in candidates:
        low = leftover.lower()
        if len(leftover.split()) < 6 or low.startswith(SIGNING_OFF):
            continue
        # The leftover has to be readable as the answer on its own. One that opens on a
        # conditional, a conjunction or the hand-off sentence of a hedge is the second half of
        # something, and a person handed it has to guess what the first half said.
        if not detail.stands_alone(leftover):
            continue
        # A question is not the step the person has not had yet: it is the thing the bot asked
        # them, and handing it back says the same sentence twice running. "my brother is a chef"
        # then "he works in town" was answered "what does a normal day look like for him?" on the
        # turn after the bot had asked exactly that.
        if leftover.rstrip().endswith("?"):
            continue
        if not any(re.search(r"\b" + step + r"\w*", low) for step in A_STEP_IN_IT):
            continue
        return leftover
    return ""


def _the_answer_again(answer, turns):
    """True when the last reply is an earlier answer of the bot's, said again.

    The memory store hands the last answer back with a short lead-in ("Sure - ...") when the person
    asks to hear it again, and nothing in that is un-had: it is the answer they have just read.
    After "come again?" over the Lisbon answer, the next line - a new fact about Sintra - was
    answered with "May is warm and busy, so book the tower and the popular restaurants ahead", the
    tail of the answer they had been given a moment before, instead of the fact being taken down.
    """
    low = " ".join(str(answer or "").lower().split())
    for one in turns[:-1]:
        earlier = " ".join(str(one.get("bot") or "").lower().split())
        if len(earlier.split()) >= 6 and earlier in low:
            return True
    return False


def takes_as_it_comes(text, memory):
    """True when the composer's own line is the answer, whatever else proposed."""
    return (fallback.reads_as_about_itself(text, memory)      # a question about the bot
            or fallback.reads_as_a_tight_week(text, memory)    # the money has run out
            # and the turn after that one, when they ask the bot to go on: the ack pool answered
            # "and" with "Alright then - good luck with it", which ends the conversation the
            # person was keeping going (`a_continuation_of_the_tight_week`).
            or fallback.a_continuation_of_the_tight_week(memory, text)
            or fallback.reads_as_small_talk(text, memory)     # "hows your day going, then"
            # the person's own figure, read in the unit of the rule the answer just named
            or quantity.the_figure_against_the_answer(text, memory) is not None
            # a move said without saying it is a glad one: the pool asks about it
            or moving.reads_as_a_move_cheered(text)
            # and the somebody to see, asked about in five words after an answer that named one
            or who_to_see.replies_to_a_who_to_see(text, memory)
            or fallback.TAKES_AS_IT_COMES(text, memory))      # a bare "why", or a report on advice


TAKES_AS_IT_COMES = takes_as_it_comes

from ..memory import again as _said_before  # noqa: E402 - applied once the module is defined

# Whatever this module answers, the last thing that happens to it is the earlier-turn
# check (bot/memory/again.replied): `answers` alone served a card again on 59 deck turns.
respond = _said_before.replied(respond)

# The last thing that happens to a reply: the composer's own two acknowledgements are turned into
# one short question about the thing the person just said. It is a wrapper rather than a branch
# inside `respond` because it needs the finished reply and because the end of the function is
# where every reader in the swarm is adding its own branch. Only "I'm listening - say more if it
# helps", "Got it. Is there anything you'd like a hand with?" and the third of that pool are
# replaced, so a card, a pool reply or a search hedge keeps its turn (bot/compose/a_detail_dropped.py).
from ..compose import a_detail_dropped as _a_detail_dropped  # noqa: E402

respond = _a_detail_dropped.turned(respond)
