"""The words an answer hands over to say, kept whole when the answer is cut down.

A lot of the knowledge base's best answers end in the words the person can send: a letter to a
landlord, a message to a neighbour, the sentence to say at a counter. Those words sit inside
quotation marks, and they have full stops of their own - a letter is two or three sentences long.

Every short form of an answer is made by cutting it at a full stop. That is right for a paragraph
of advice, and wrong for a quoted letter: the cut landed inside the quotes and the person was
given

    Keep it short, dated and specific, and ask for a date: "Hi — I reported the boiler on [date]
    and nothing has been done.

- half a letter, with the opening quotation mark never closed. Said after "how do i ask him
again", that is what the bot printed. Half a quotation is not a shorter version of the answer,
it is a broken one.

So the two marks are counted, and a cut that stops with a quote still open is carried on until the
quote closes. Nothing else about the cut changes: a reply with no quotation in it comes back
exactly as the caller would have cut it.
"""


import re


def left_open(said):
    """True when `said` opens a quotation it does not close.

    Each convention is counted on its own: an odd number of straight quotes, or more curly openers
    than closers. Cheap, and it does not need to know which one an entry writes in.
    """
    said = str(said or "")
    if said.count('"') % 2:
        return True
    return said.count("\u201c") > said.count("\u201d")


def closed(said, rest, whole=""):
    """`said` carried on through `rest` until the quotation in it closes.

    `said` is the short form the caller cut, `rest` the sentences after it in the same order, and
    `whole` the answer they came from. A quote that never closes inside the answer cannot be cut
    short at all, and `whole` is what comes back: it is long, but it is not broken.
    """
    said = str(said or "").strip()
    if not left_open(said):
        return said
    for part in rest:
        said = (said + " " + str(part or "").strip()).strip()
        if not left_open(said):
            return said
    return str(whole or said).strip()


# A full stop inside a name, a title or an abbreviation is not the end of a sentence. The scary
# shelf reads "and *Inside No. 9* for half-hour creepers", and the sentence that answers "how long
# did i want it" was cut at "No." - the person was handed "9* for half-hour creepers." The word
# before the stop is short and capitalised, and the part after it opens on a figure, which no
# sentence in these rows does: "Volume. 2" is a name, "Ring 111. 2 hours later" is not read here.
NAME_END = re.compile(r"\b(?:no|nos|vol|vols|ch|pt|pp|fig|e\.g|i\.e|etc|vs|dr|mr|mrs|ms|prof|st|"
                      r"al|inc|ltd|co|dept|tel|ref)\.$", re.I)
OPENS_ON_A_FIGURE = re.compile(r"^[\d*\u00a3$\u20ac]")


def a_name(text, start, end):
    """True when the full stop ending `text[start:end]` is part of a name rather than a sentence."""
    before = str(text[start:end]).strip()
    if not before.endswith("."):
        return False
    if not NAME_END.search(before):
        return False
    after = str(text[end:]).lstrip()
    return bool(OPENS_ON_A_FIGURE.match(after))


def sentences(text, splitter):
    """`splitter`'s sentences, with a quotation or a name kept in one piece.

    The sentence splitters in this package cut at a full stop and a space, which is right for a
    paragraph of advice and wrong inside a quoted letter: "...nothing has been done. Please let
    me know when an engineer can come" is one thing to hand over and two sentences to a splitter.
    Half of it reached the person as a sentence of its own - "how do i ask him again" after the
    landlord answer came back as the first half of the letter, quote open. A part that opens a
    quotation belongs with the parts after it until the quote closes, so it is only a sentence
    when the quote in it is finished.
    """
    text = str(text or "")
    if not hasattr(splitter, "finditer"):
        return [part.strip() for part in splitter.split(text) if str(part).strip()]
    parts, start = [], 0
    for end in splitter.finditer(text):
        if a_name(text, start, end.start()):
            continue
        parts.append(text[start:end.start()].strip())
        start = end.end()
    parts.append(text[start:].strip())
    parts = [part for part in parts if part]
    out = []
    for part in parts:
        if out and left_open(out[-1]):
            out[-1] = (out[-1] + " " + part).strip()
        else:
            out.append(part)
    return out
