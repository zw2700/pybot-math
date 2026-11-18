"""A yes/no about a figure the bot itself gave: "so is eight weeks still right".

The figure is the answer's - the chat already said eight weeks - and the question is whether it
still stands. Nothing in the line names a thing of its own, so the knowledge base read the words
it could see and answered from an entry about something else: "so is eight weeks still right"
after a 5k plan got "Ask in writing and name what you want: a refund, a repair, or money for the
trouble. Once eight weeks pass..." - a consumer-complaint entry, reached by the figure's words.

The reading and the wording live in `bot/memory/stands.py`: the answer is the figure with the
reason the chat already gave for it, because that is the sentence the bot used and a friend who is
asked "is that still right" says where the number came from rather than looking it up again.

This module sits above the knowledge base (0), because the entry that answered these lines was the
knowledge base reading a figure as a subject, and below the safety band and the loss and grief
modules, which keep their turns: "is three sessions a week still right" during a bereavement is
not a question about the figure. It returns None on every line that is not a yes/no about a figure
of this chat's own answers.
"""
from ..memory import stands

PRIORITY = 1000  # above the knowledge base, below loss (2000), grief (2100) and safety (9000)


def respond(text, memory):
    """The reply to a yes/no about a figure the bot gave, or None for every other line.

    Two shapes: a figure in the line ("so is eight weeks still right"), and a change with no figure
    in it ("does that change the time?", after "actually its a veggie one, no mince"). Both are the
    chat's own answer handed back, and both are here because the answer is the same figure.
    """
    return stands.reply_for(text, memory) or stands.change_reply(text, memory)


def takes_as_it_comes(text, memory):
    """Only on a yes/no about a figure of this chat's own answers, and nowhere else."""
    try:
        return bool(stands.the_figure_asked_about(text, memory)
                    or stands.the_change_asked_about(text, memory))
    except Exception:  # noqa: BLE001 - a hook that raises claims nothing
        return False


# The arbiter reads the declaration by this name (`bot/modules/arbiter.py: DECLARED_AS_IT_COMES`),
# the way every other module declares it. The knowledge base declares on the same line - a card
# matched the figure's words - and this is the module that read what the line is about.
TAKES_AS_IT_COMES = takes_as_it_comes
