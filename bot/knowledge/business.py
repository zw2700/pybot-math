"""Running your own work: going self-employed, pricing it, invoicing and getting paid.

The knowledge base already answers "how do i register as self employed" and "how do i file a
self assessment". Everything round them was a shrug: what to do first, what to charge, where
the first client comes from, what an invoice has to say, what to do when a client does not pay,
whether to register for VAT, whether a business account is needed, sole trader against a limited
company, and what a contract has to contain.

The entries are keyed by the thing being asked about - the step, the document, the payment -
not by the words "business" and "how", so a line reaches the same answer whichever way it is
put: "how do i price my work", "what should i charge", "how do i work out a day rate".

These are everyday questions from people who have just started selling something, so every
answer has a number in it: the VAT threshold, the filing date, what counts as one contract,
what a claim costs. Wording about money is deliberately plain and the numbers are the ones that
have been stable for years; where a figure moves with the Bank of England it is named as a
formula rather than as a number, because a stale number is worse than a rule.
"""

from .lookup import entry

ANSWERS = ("money", "work")


# Words that name the business itself, so a line about a phone contract, a tenancy or a job
# offer never reaches these rows. The key words below are ordinary English ("charge", "rate",
# "contract", "account"), and each of those is a commoner word in some other domain.
NOT_A_BUSINESS = (
    # a phone, a gym, a tenancy and a subscription are contracts too
    "phone", "mobile", "sim", "broadband", "energy", "gas", "electric", "electricity",
    "water", "gym", "tenancy", "landlord", "rent", "mortgage", "lease", "insurance",
    "car insurance", "pet insurance", "boiler", "council tax", "tv licence", "licence fee",
    "subscription", "streaming", "netflix", "spotify", "train", "parking", "ticket", "flight",
    # an employment contract and a job offer are the job's, not the business's
    "employer", "employee", "employees", "boss", "manager", "colleague", "hr", "job offer",
    "job interview", "interview", "redundancy", "notice period", "payslip", "paye", "payroll",
    "apprenticeship", "zero hours", "sick pay", "holiday pay", "maternity", "paternity",
    # a bill for something already bought, and every consumer refund
    "refund", "return", "returns", "warranty", "guarantee", "faulty", "shop", "supermarket",
    "online order", "delivery", "parcel", "courier", "takeaway", "restaurant", "hotel",
)

# The self-employed sense of "charge", "rate" and "invoice". A line has to name the work, the
# client or the money it is asking about, or it is somebody else's row: "how much should i
# charge my phone" is a battery question and "what rate is my boiler" is not a day rate.
BUSINESS_ASK = (
    "work", "works", "working", "client", "clients", "customer", "customers", "freelance",
    "freelancer", "freelancing", "self employed", "self-employed", "sole trader", "business",
    "businesses", "trade", "trades", "service", "services", "job", "jobs", "project",
    "projects", "rate", "rates", "day rate", "hourly rate", "hourly", "invoice", "invoices",
    "invoicing", "quote", "quotes", "charge", "charging", "contract", "contracts", "vat",
    "company", "limited company", "limited", "ltd", "start up", "startup", "my own",
    "for myself", "on my own", "as a freelancer", "as a sole trader",
)

# The neighbours whose answers are already good and must not move: the start of a job, the
# employee's own tax, a benefit, a trade's bad workmanship, and the complaint about a shop.
NOT_THIS = NOT_A_BUSINESS + (
    "universal credit", "benefits", "child benefit", "pip", "esa", "student loan", "student",
    "pension", "pensioner", "graduate", "graduate scheme", "internship", "work experience",
    "cv", "interview", "apprenticeship", "university", "college", "exam", "course",
    "builder", "plumber", "electrician", "roofer", "decorator", "tradesman", "handyman",
    "doctor", "gp", "hospital", "nhs", "dentist", "school", "teacher", "nursery", "council",
    "my ex", "husband", "wife", "partner", "flatmate", "neighbour", "noise",
)

# A trade word is in the avoid list because "my plumber says the boiler is finished, how much
# should i charge" is a question about somebody else's work. The same word is the row's own
# subject when the person is the trade: "i want to start out on my own as a plumber", "how do i
# go self employed as a builder", "can i be a sole trader and a roofer". Those lines were the
# search shrug on main, and the first of them was answered with the make-friends card because
# "on my own" also means lonely. So the going-alone words are read here, and they have to be
# said: a trade named in any other line still stands the row down.
TRADES = ("builder", "plumber", "electrician", "roofer", "decorator", "tradesman", "handyman",
          "plasterer", "carpenter", "joiner", "painter", "landscaper", "locksmith",
          "gas engineer", "heating engineer")
_GOING_ALONE = (
    "my own", "for myself", "self employed", "self-employed", "sole trader", "my own boss",
    "go it alone", "going solo", "go solo", "freelance", "in business", "working for myself",
)
# Everything NOT_THIS says apart from the trade words, for the row that reads a trade as its own
# subject.
NOT_THIS_ELSEWHERE = tuple(word for word in NOT_THIS if word not in TRADES)


def _a_trade_is_their_own(understood):
    """True unless the line is about somebody else's trade work."""
    if not isinstance(understood, dict):
        return True
    text = " " + str(understood.get("clean") or understood.get("text") or "").lower() + " "
    if not any(word in text for word in TRADES):
        return True
    return any(word in text for word in _GOING_ALONE)


def _the_start_out_names_no_thing(understood):
    """True unless the line says what it is starting out *into*.

    "How do i start out in running" is a question about running, and "how do i start out in
    photography" about photography: both name a thing, and both were handed the sole-trader
    answer because the row reads the two words "start out" as a business. A bare "how do i start
    out" names nothing and is the bare ask ("pick the single next step").

    The reader is the memory lane's, so that the row and the start ask are the same question about
    the same words rather than two lists kept in step.
    """
    from ..memory.repeat import _starting_out_names_a_thing

    if not isinstance(understood, dict):
        return True
    text = " " + str(understood.get("clean") or understood.get("text") or "").lower() + " "
    if not _starting_out_names_a_thing(text):
        return True
    # A line that says the business words as well is still this row's: "start out on my own",
    # "start out freelance", "start out in business" all name something after "out" and all mean
    # the going-alone answer, and the loneliness card had "on my own" before this row did.
    return any(word in text for word in _GOING_ALONE + (
        "business", "trade", "company", "firm", "shop", "sole trader"))


def _the_person_is_the_row(understood):
    """Both guards of the start-a-business row: their own trade, and no thing started out into."""
    return _a_trade_is_their_own(understood) and _the_start_out_names_no_thing(understood)


ENTRIES = [
    # "how do i start a small business" and "how do i set up on my own" were the search shrug:
    # the registration rows answer the paperwork and nothing answered what to do first.
    entry("start-a-business",
          (("start a business", "start my own business", "starting a business",
            "start up a business", "set up a business", "set up on my own", "start trading",
            "start working for myself", "work for myself", "be my own boss", "go it alone",
            "start a small business", "small business", "new business",
            # "start out" on its own is not a business: "how do i start out in running" and "how
            # do i start out in photography" were both handed the sole-trader answer on the two
            # words "start out", and neither is a question about a business. The phrases that do
            # carry it are the ones that say what is being started out into.
            "start out on my own", "start out freelance", "start out self employed",
            "start out in business", "start out working for myself", "start out selling",
            # a bare "start out" is the bare ask; what follows it is the subject, and the guard
            # below stands this row down for those lines
            "start out",
            # a business started beside a job is the same first step, and "how do i start a side
            # business" was a search shrug on main: "start a business" does not match it
            "side business", "side hustle", "side hustle", "on the side", "second income",
            "extra income", "start a side", "sell my own", "sell something",
            "start a company", "set up a company",
            # a trade says its own name where "business" would go ("how do i start my own
            # plumbing business"), and the phrase "start my own" is the ask in all of them
            "start my own", "set up my own", "my own trade", "my own firm", "my own shop",
            # "im thinking of going self employed" is the same question said as a musing, and it
            # met a hedge ("worth planning rather than rushing into") on main
            # not "leave my job" or "quit my job": "im thinking of quittin my job" is the
            # resignation letter, and the words are the same. The business words carry it.
            "going self employed", "go self employed", "going solo"),
           ("how do i", "how to", "where do i start", "what do i need", "first steps",
            "start", "starting", "begin", "set up", "should i", "do i need", "need to",
            "thinking of", "thinking about", "considering", "what should i know",
            "is it worth")),
          "Sell something before you register anything: one paying customer tells you more than "
          "a plan, and you can trade as a sole trader from the day you start. Then do three "
          "things in this order - register as a sole trader with HMRC (by 5 October after the "
          "end of your first tax year), open a second bank account so business money is not "
          "mixed with rent and shopping, and keep every receipt and invoice from day one, "
          "because the expenses are what cut the tax bill. Tell HMRC the date you started, not "
          "the date you got round to it. A name, a phone number and one clear service are "
          "enough to begin: a website and a logo can wait until someone is paying you.",
          avoid=NOT_THIS_ELSEWHERE + ("vat", "limited company", "ltd", "incorporate", "franchise",
                                      "licence", "premises", "plan", "business plan",
                                      # growth and marketing are the row below, not the first step
                                      "market", "marketing", "advertise", "advertising", "grow",
                                      "growing", "scale", "more customers", "more clients"),
          ask=BUSINESS_ASK + ("how do i", "how to", "where do i start", "what do i need",
                              "first steps", "start", "starting", "begin", "set up"),
          guard=_the_person_is_the_row,
          bias=1),

    # "how do i grow my business" and "how do i market my small business" were the shrug and
    # the first-step answer. They are the next question, and the answer is not an advert.
    entry("grow-your-business",
          (("grow my business", "grow the business", "growing my business", "more customers",
            "more clients", "market my business", "marketing", "advertise", "advertising",
            "get more work", "scale up", "expand my business", "bring in more work",
            "win more work", "repeat business", "referrals",
            # "how do i scale my business" and "what does scaling a business mean" are this
            # question in the word people use once the work is steady: "scale" alone was the
            # search line, and "what is scaling up in business" was answered with the music
            # theory of a scale because the word stands on its own in "what is".
            "scale my business", "scale the business", "scale your business",
            "scaling a business", "scaling my business", "scaling up a business",
            "scaling up in business", "scale a business", "scale it up",
            "grow the company", "growing the company", "expand the business"),
           # the same question asked to be explained: "what is scaling up in business" and
           # "what does scaling a business mean" found only the music glossary, because a
           # bare "what is" was enough to reach the ladder of notes
           ("how do i", "how to", "how do", "where do i", "start", "get", "find", "more",
            "should", "best way", "what should", "what is", "whats", "what does", "mean",
            "means", "meaning", "explain")),
          "The cheapest new work is the client you already have: go back to everyone you worked "
          "for in the last year with one specific offer - a set number of hours a month, or the "
          "service you did not offer them last time. A past client is far more likely to say yes "
          "than a stranger. Then ask each happy client for one name and for a review in writing, "
          "and put those words where people actually look. Pick one channel and be there "
          "consistently rather than on four occasionally, and put your prices up 10% on new work "
          "before you think about hiring anyone.",
          avoid=NOT_THIS + ("stock market", "shares", "crypto", "plant", "tomato", "hair",
                            "nails", "garden", "lawn", "child", "baby", "beard",
                            # "scale up" is also what a kettle, a boiler and a shower head do:
                            # "how do i stop my kettle scaling up" was this row, and the answer
                            # was to ring the clients you already have. A machine in the line is
                            # not a business, so the appliance words stand this row down.
                            "kettle", "kettles", "limescale", "descale", "descaler", "boiler",
                            "boilers", "shower head", "showerhead", "shower", "washing machine",
                            "dishwasher", "tumble dryer", "radiator", "radiators", "tap water",
                            "water pressure", "central heating", "scale in the", "scale in my",
                            # and "scale up" is how a recipe grows too: "how do i scale up a recipe
                            # for 20 people" was the marketing plan
                            "recipe", "recipes", "cooking", "baking", "oven",
                            # "how do i unsubscribe from marketing emails" is the inbox row's:
                            # an unsubscribe link is not a growth channel
                            "unsubscribe", "mailing list", "newsletter", "newsletters", "inbox",
                            "spam", "junk mail"),
          ask=BUSINESS_ASK + ("how do i", "how to", "how do", "where do i", "start", "get",
                              "find", "more", "should", "best way", "what should",
                              # "what is scaling up in business" and "what does scaling a
                              # business mean" are the same question asked to be explained,
                              # and "what is" was all the music glossary needed: a scale in
                              # business was answered with the ladder of notes.
                              "what is", "whats", "what does", "mean", "means", "meaning",
                              "explain"),
          bias=1),

    # "how do i price my work", "what should i charge" and "how do i work out a day rate" were
    # all the shrug, and it is the question every new freelancer asks first.
    entry("price-your-work",
          (("price my work", "price my services", "pricing", "what should i charge",
            "how much should i charge", "how much do i charge", "what do i charge",
            "day rate", "hourly rate", "set my rates", "set my rate", "work out my rate",
            "charge for my time", "charge for my work", "how much is my time worth",
            "price myself", "undercharging", "charge more"),
           BUSINESS_ASK),
          "Start from the money you need, not from what feels cheeky: add up your yearly costs "
          "(tools, insurance, software, travel, a phone) and the income you want to take home, "
          "add about a third on top for tax and quiet weeks, then divide by the days you can "
          "actually bill - about 220 a year if you work full time, and far fewer if you spend "
          "half the week on admin and chasing work. That gives a day rate; an hourly rate is "
          "that divided by six or seven. Then check three people doing the same job and put "
          "yourself in the middle. Quote a fixed price for a fixed job, not hours, and take a "
          "deposit of a third or a half up front.",
          avoid=NOT_THIS + ("how much does it cost", "battery", "boiler", "electricity",
                            # a fee a shop charged the person is a consumer complaint, not a
                            # price to set: "i was charged a hidden fee that wasnt in the price"
                            # was given the day-rate answer, which is advice to the seller rather
                            # than to the buyer, and `unexpected-fee` says what to do about it
                            "hidden fee", "hidden fees", "hidden charge", "hidden charges",
                            "booking fee", "admin fee", "administration fee", "service fee",
                            "processing fee", "card fee", "surcharge", "extra fee",
                            "extra charge", "handling fee", "convenience fee", "drip pricing",
                            # "charged" alone is left out on purpose: "the price on the shelf
                            # was less than they charged me" is a shop overcharging, and the
                            # day-rate card stepping aside for it hands the line to the bank's
                            # overdraft card, which is worse than either
                            "charged a fee", "charged an extra", "charged me a fee",
                            "at the checkout", "on the bill", "added a charge", "added a fee",
                            # telling existing clients about a rise is work.py's own card
                            "raise my prices", "raise my rates", "put my prices up",
                            "prices up", "price rise", "raising prices", "increase my rates",
                            "increase my prices", "tell clients", "tell a client",
                            "tell my client", "tell my clients",
                            "petrol", "diesel", "taxi", "uber", "delivery", "postage",
                            "how much should i charge my phone", "how much should i tip",
                            # a VAT question is the money domain's: "do i add vat to my prices"
                            # was this row's day-rate answer on the word "prices"
                            "vat", "value added tax"),
          ask=BUSINESS_ASK,
          bias=1),

    # Whether to go at all comes before how to register and how to price: "should i go
    # freelance" and "should i become self employed" were the composer's "That's your call, not
    # mine", and "is it worth going freelance" was the SIPP, which answers a person who has
    # already decided. This is the decision, and the decision is a money test.
    entry("going-freelance",
          (("go freelance", "going freelance", "become freelance", "be freelance", "freelancing",
            "go self employed", "go self-employed", "become self employed",
            "become self-employed", "be my own boss", "work for myself", "go it alone",
            "leave my job to", "start freelancing", "start out freelance"),
           ("should", "worth", "is it", "is it worth", "thinking of", "thinking about",
            "considering", "not sure", "ready", "shall", "how do i know", "signs", "advice",
            "pros and cons")),
          "Test it on the money before anything else: work out what you need to live on for a year, add about a third for tax, your own kit and quiet weeks, and check you have one client who will pay it. Most people who last had six months of savings and a signed first job before they left. Start as a sole trader - it is free to register with HMRC, and a limited company can wait until the work is steady.",
          avoid=NOT_THIS + ("pension", "pensions", "sipp", "retire", "retirement", "tax return",
                            "self assessment", "register", "registering", "invoice",
                            "invoice them", "day rate", "first client", "first customer",
                            "chase an invoice", "when do i pay tax"),
          bias=1),

    # "how do i get my first client" is the second question every new freelancer asks, and the
    # answer is not a marketing plan: it is the people who already know the work.
    entry("first-clients",
          (("first client", "first clients", "first customer", "first customers",
            "get clients", "find clients", "win clients", "get customers", "find customers",
            "get work", "find work", "more clients", "get more work", "find more clients",
            "clients from", "customers from"),
           ("how do i", "how to", "where do i", "where", "how do", "start", "starting",
            "first", "get", "find")),
          "The first three clients come from people who already know your work: a former "
          "employer or colleague, a friend who runs something, the local shop, a group you are "
          "already in. Pick one service you can name in a sentence, then tell twenty people "
          "you have started and what you charge - not a general announcement, one message each. "
          "Offer the first job small and priced so saying yes is easy, do it fast and well, "
          "and end every job by asking that client who else needs it. Two happy clients who "
          "recommend you beat any advert you could afford at this stage.",
          avoid=NOT_THIS,
          ask=BUSINESS_ASK + ("how do i", "how to", "where do i", "where", "how do",
                              "start", "starting", "first", "get", "find"),
          bias=1),

    # "how do i write an invoice" and "what should an invoice say" were the shrug, and the
    # answer is a short list of things a court would want to see.
    entry("invoice-a-client",
          (("invoice", "invoices", "invoicing", "bill a client", "bill my client",
            "bill the client", "send a bill"),
           ("write", "writing", "written", "how do i", "what should", "what to put",
            "what do i put", "template", "checklist", "need", "needs", "send", "make",
            "include", "say",
            # "what has to be on an invoice" is the same question as "what should one say"
            "has to be", "has to", "must be", "must have", "got to be", "goes on")),
          "An invoice needs seven things: your name and address, the client's name and "
          "address, a number of its own (0001, 0002 - never reused), the date, what you did "
          "with the dates you did it, the amount with the payment terms on it, and your bank "
          "details. Add your VAT number once you are registered, and put the terms in words - "
          "\"payment due within 14 days of the invoice date\" - plus what happens if it is "
          "late. Keep the same number series for ever and send it the day the work finishes, "
          "not at the end of the month: an invoice sent a fortnight late is paid a fortnight "
          "late. A PDF named with the number and the client is enough; a template in a word "
          "processor is all most people need.",
          # The chase is the other row's question: `client-not-paying` keys "unpaid" and
          # "late", and this row keys the bare "invoice" plus the bare "how do i", so
          # "how do i chase an unpaid invoice" was the same score on both and the earlier entry
          # won it - the invoice contents, when the person's invoice was written and ignored.
          # Everything a chasing line says, named here: what to put on an invoice never says
          # someone has not paid.
          avoid=NOT_THIS + ("energy", "water", "broadband", "council", "hospital", "nhs",
                            "unpaid", "chase", "chasing", "chas", "overdue", "not paid",
                            "not been paid", "hasn't paid", "hasnt paid", "will not pay",
                            "won't pay", "wont pay", "refuses", "owes me", "owe me",
                            "late payment", "late payments", "not paying", "remind",
                            "reminder", "reminders", "still waiting", "never paid",
                            "ignored", "ignoring", "debt", "debtor", "bad debt",
                            # how long to KEEP an invoice is a records question (money's
                            # five-year answer), not what goes on one: the ask list holds the
                            # bare "need", so "how long do i need to keep invoices" matched
                            # here and lost the five-year answer (violet-moss, #5946)
                            "keep", "keeping", "how long", "how many years", "retain",
                            "records", "archive", "shred", "dispose"),
          ask=("invoice", "invoices", "invoicing", "bill a client", "bill my client",
               "bill the client", "send a bill", "what has to be on", "what goes on",
               "on an invoice", "on a invoice", "what should be on"),
          bias=1),

    # "how do i get paid when a client won't pay" was the shrug, and "what can i do about a
    # late payment" was the consumer card: a business debt has its own steps and its own law.
    entry("client-not-paying",
          (("client", "clients", "customer", "customers", "invoice", "invoices", "bill",
            "payment", "payments"),
           ("won't pay", "wont pay", "not paying", "didn't pay", "didnt pay", "hasn't paid",
            "hasnt paid", "refusing to pay", "refuses to pay", "late payment", "late payments",
            "overdue", "not been paid", "still not paid", "never paid", "chase the payment",
            "chasing payment", "owes me", "owe me", "bad debt", "unpaid")),
          "Chase it in writing and in steps, because the paper is what wins later: on the day "
          "it is due, one short email with the invoice attached and a new date; a week later, a "
          "firmer one that says what happens next; after that, a letter before action giving 14 "
          "days. Then use the money claim online, which handles claims up to £10,000 for a fee "
          "that is added to what they owe. A business debt also carries statutory interest at "
          "8% above the Bank of England base rate from the due date, plus a fixed sum of £40 to "
          "£100 depending on the size of the debt - say so in the letter, because it is enough "
          "to make most late payers move. Stop doing new work for them the day the first "
          "payment is missed, and never hand over the finished work before the deposit.",
          avoid=NOT_THIS + ("refund", "shop", "company owes me", "energy", "broadband",
                            "friend", "family", "landlord", "rent", "ex", "loan", "borrow"),
          ask=("client", "clients", "customer", "customers", "invoice", "invoices",
               "business", "freelance", "freelancer", "self employed", "self-employed",
               "sole trader", "contractor", "my work"),
          bias=1),

    # "do i need to register for vat" was the shrug, and it has a threshold, a date and a
    # consequence: the price goes up by a fifth.
    entry("vat-registration",
          (("vat", "value added tax", "vat registered", "vat registration", "vat number",
            "vat return", "vat threshold"),
           ("register", "registering", "registration", "do i need", "when", "threshold",
            "how much", "have to", "need to", "charge", "claim", "claim back", "already",
            "over", "go over", "went over",
            # "do i add vat to my prices" and "is vat on top of my price" are this row's, and
            # the pricing card was taking them on the word "prices"
            "add", "adding", "added", "on top", "include", "including", "included")),
          "Register when your sales go over £90,000 in any rolling twelve months, or when you "
          "think they will in the next thirty days; do it within 30 days of the end of the "
          "month you went over. Registering means you add 20% VAT to your prices and hand it "
          "over, but you also reclaim the VAT on what you buy for the business, so if your "
          "customers are other businesses it usually costs you nothing. Returns are normally "
          "quarterly and have to be filed from digital records. You can ask to deregister if "
          "your sales fall under £88,000.",
          # "how much vat do i charge" is the rate, and the money domain answers it with 20%:
          # this row keys a bare "vat" plus "how much" and "charge", which is how much VAT a
          # person hands over as well as how much sales a person may make before registering.
          avoid=NOT_THIS + ("car", "van", "fuel", "receipt", "refund", "shop", "price",
                            "how much is vat", "what is vat", "how much vat", "vat rate",
                            "rate of vat", "what rate", "vat on top", "charge vat on"),
          ask=("vat", "value added tax", "vat registered", "vat registration", "vat number",
               "vat return", "vat threshold"),
          bias=1),

    # "do i need a business bank account" is asked by everyone in the first month, and the
    # answer is no-but-yes.
    entry("business-bank-account",
          (("business bank account", "business account", "separate bank account",
            "separate account", "second bank account", "bank account for my business",
            "sole trader account", "business banking", "separate business"),
           ("need", "do i", "should i", "open", "how", "worth", "have to", "get",
            "set up", "why")),
          "As a sole trader you do not legally need one, and you should still open one: a "
          "separate account means every payment in is income and every payment out is a cost, "
          "which is most of a tax return done already. Mixing the two is the reason people "
          "spend a weekend with a shoebox. Free business banking for 12 to 18 months is normal "
          "at the moment, so compare two or three before you pick, and check the monthly fee "
          "afterwards and the cost of paying cash in. A second personal account works if no "
          "bank will take you yet. A limited company does have to have its own account.",
          avoid=NOT_THIS + ("switch", "switching", "overdraft", "joint", "savings",
                            "isa", "child", "student", "basic"),
          ask=("business bank account", "business account", "separate bank account",
               "separate account", "second bank account", "bank account for my business",
               "sole trader account", "business banking", "business", "sole trader",
               "self employed", "company", "ltd"),
          bias=1),

    # "should i be a limited company" is the decision people get stuck on for weeks.
    entry("limited-or-sole-trader",
          (("limited company", "limited companies", "ltd", "incorporate", "incorporating",
            "limited or sole trader", "sole trader or limited", "company or sole trader",
            "sole trader or a company", "register a company", "set up a limited company",
            # "start" is the same verb as "set up", and "how do i start a limited company" was a
            # search shrug on main
            "start a limited company", "start a ltd", "start a limited", "start my own company"),
           ("should i", "which", "difference", "worth", "better", "set up", "become",
            "be a", "choose", "why", "do i need", "when",
            # "start" is the same verb as "set up" here
            "start", "starting", "how do i",
            # "what is a sole trader" is the front door to the same decision
            "what is", "what does", "mean", "plain english")),
          "A sole trader is the simplest thing that works: you and the business are the same "
          "person, you file a self assessment, your accounts stay private, and if it goes wrong "
          "you are personally on the hook for the debts. A limited company is a separate legal "
          "person, so your own money is mostly protected, but you file accounts at Companies "
          "House where anyone can read them, pay corporation tax on profits (19% to 25%), and "
          "take money out as a salary through payroll and as dividends, which means an "
          "accountant is worth having. It costs about £50 to set one up and a few hundred a "
          "year to run. Most people start as a sole trader and move over when profits are "
          "steady, when they take on a contract with real risk, or when they hire someone.",
          avoid=NOT_THIS + ("company car", "company name", "dissolve", "strike off",
                            "close my company", "company pension", "shares"),
          ask=("limited company", "limited companies", "ltd", "incorporate", "incorporating",
               "limited or sole trader", "sole trader or limited", "company or sole trader",
               "sole trader or a company", "register a company", "set up a limited company",
               "start a limited company", "start a ltd", "start a limited",
               "limited company", "ltd",
               "business", "self employed", "sole trader"),
          bias=1),

    # "how do i write a contract for a client" was the shrug, and for a one-person business a
    # contract is a page, not a document from a solicitor.
    entry("client-contract",
          (("contract", "contracts", "agreement", "write a contract", "simple contract",
            "client agreement", "terms of business", "scope of work", "quote for a job"),
           ("client", "clients", "customer", "customers", "freelance", "freelancer",
            "business", "self employed", "my work", "job", "write", "need", "simple",
            "how do i", "what should")),
          "One page is enough for a one-person business, and six lines cover almost everything: "
          "who you both are, exactly what you will do and by when, what it costs and when it is "
          "paid, what is included and what costs extra, who owns the finished work, and how "
          "either of you can end it. Add what happens if they change their mind - a set hourly "
          "rate for changes is the line that saves the job - and ask for a deposit of a third or "
          "half before you start. A quote they answer with \"yes, go ahead\" in an email is a "
          "contract already, so keep that email; you do not need a solicitor for a job worth a "
          "few hundred pounds, only for premises, staff or work that could hurt someone.",
          avoid=NOT_THIS + ("tenancy", "employment contract", "employment", "workplace",
                            "settlement", "nda", "lease", "mobile", "gym", "wedding",
                            "divorce", "prenup", "marriage"),
          ask=("client", "clients", "customer", "customers", "freelance", "freelancer",
               "business", "self employed", "sole trader", "contractor", "my work",
               "what should be in", "what goes in", "in a contract", "what to put in",
               "what should a contract", "contract template", "contract clauses"),
          bias=1),
]
