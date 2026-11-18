"""The words of money: the everyday terms on a payslip, a bank statement and a loan offer.

People meet these words in a contract or a headline and ask what they mean. `money.py` answers
the decisions (can I afford this, how much is a deposit, should I rent or buy); this domain
answers the vocabulary the questions are made of, one entry per word people actually ask about.

The keys are the word itself, gated to a definition ask wherever the bare word also turns up in
another question: "stock" is soup as well as shares, "fixed rate" is a tariff as well as a
mortgage, and "council tax band" must not take a plain "how much is council tax" line, which is
a bill to work out rather than a word to explain.
"""

from bot.knowledge.lookup import entry

ENTRIES = [
    entry("apr", (("apr", "a p r"), ("what", "whats", "mean", "means", "stand", "explain",
                                     "how", "work", "works", "rate", "higher", "lower")),
          ("APR is the interest plus the fees, worked out over a year, so it is the number to "
           "compare two offers on rather than the headline rate. A £1,000 loan repaid over a year "
           "at 20% APR costs about £1,110 in total. A 0% on purchases card has no interest, but a "
           "cash withdrawal from it starts at about 25% APR from day one."),
          avoid=("bank holiday", "weather", "month")),
    entry("inflation", (("inflation",), ("what", "whats", "mean", "means", "explain", "why",
                                         "cause", "causes", "rate", "work", "works", "high",
                                         "lower", "bring")),
          ("Inflation is how much more things cost than a year ago, as a percentage: at 3% a £100 "
           "shop costs £103 next year, and £100 in a savings account at 2% buys less than it did. "
           "The Bank of England aims for 2% and moves interest rates to get back to it, which is "
           "why a mortgage or a savings rate changes when inflation does.")),
    entry("payday-loan", (("payday", "payday loan", "payday loans", "payday lender"),
                          ("loan", "loans", "borrow", "borrowing", "lender", "interest", "apr",
                           "cost", "rollover")),
          ("A payday loan is a small, short loan at an enormous rate: £100 for a month can cost "
           "£120 to repay, an APR of over 1,000%. The regulator caps it at 0.8% a day and no more "
           "than double the original loan in total. If it is food or rent you need, a council "
           "crisis grant, a credit union or a repayment plan with the bill is the cheaper route."),
          bias=1,
          # "is a payday loan a good idea" is the advice entry's line, and its answer opens "Don't"
          ask=("what is", "whats", "what are", "mean", "means", "explain", "how does",
               "how much does", "why is", "why are", "define")),
    entry("current-account", (("current account", "current accounts", "everyday account"),
                              ("what", "whats", "mean", "means", "open", "switch", "best",
                               "difference", "overdraft", "worth")),
          ("A current account is the everyday one: your pay goes in and the bills, the card and the "
           "cash come out, and it comes with a card and direct debits. A savings account pays more "
           "interest but has no card and no direct debits, so the two do different jobs."),
          # "should i open a current account" is the how-to (what to bring to the branch), which
          # another entry answers, so this one stays a definition of the word.
          avoid=("open", "opening", "opened", "switch", "switching", "close", "closing")),
    entry("overdraft-meaning", (("overdraft", "overdrafts", "overdrawn"),
                        ("what", "whats", "mean", "means", "charge", "charges", "cost", "fee",
                         "fees", "arranged", "unarranged", "bank", "pay", "avoid")),
          ("An overdraft is spending more than the current account holds. An arranged one is agreed "
           "with the bank and usually costs a set fee or a monthly rate; an unarranged one costs "
           "more and is reported to the credit file after a few weeks. Most banks now charge a "
           "flat monthly fee for an arranged overdraft, so ask for the fee per month, not the APR.")),
    entry("income-tax", (("income tax", "tax code", "personal allowance"),
                         ("what", "whats", "mean", "means", "rate", "rates", "band", "bands",
                          "threshold", "allowance", "how", "pay", "worked", "explain")),
          ("Income tax is taken from your pay before it reaches you. In England, Wales and Northern "
           "Ireland you pay nothing on the first £12,570, 20% from there to £50,270, 40% up to "
           "£125,140 and 45% above, and Scotland has its own five bands. On a £30,000 salary the "
           "tax is about £3,486 a year, and a tax code on your payslip is what tells payroll how "
           "much to take."),
          ask=("what is income tax", "whats income tax", "what does income tax", "income tax mean",
               "income tax explained", "explain income tax", "how does income tax work",
               "income tax rate", "income tax rates", "income tax band", "income tax bands",
               "income tax threshold", "income tax allowance", "what is a tax code",
               "personal allowance", "what is the income tax")),
    entry("self-assessment", (("self assessment", "self-assessment", "tax return", "tax returns"),
                              ("what", "whats", "mean", "means", "who", "need", "needs", "file",
                               "filing", "deadline", "when", "must", "do", "how")),
          ("Self assessment is the tax return you file yourself when tax is not taken from a "
           "payslip: self-employed earnings over £1,000, rental income, big savings interest or "
           "dividends, or income over £150,000. Register by 5 October after the tax year ends, file "
           "online by 31 January and pay by the same day; a first late filing is £100."),
          # side income under the trading allowance is a narrower question with its own answer
          # "sell" is not in this list: it is one edit from "self", and the slip repair reads
          # "what is a self assessment" as a misspelling of it and drops the entry.
          avoid=("trading allowance", "side income", "side work", "side hustle", "ebay",
                 "vinted")),
    entry("vat", (("vat",), ("what", "whats", "mean", "means", "rate", "charge", "charged",
                             "pay", "add", "include", "included", "claim", "back")),
          ("VAT is the tax added to most things you buy: 20% of the price before tax, so a £10 item "
           "is £12 with VAT. Home energy and some home work is 5%, and most food, children's "
           "clothes and books are zero-rated. A price marked \"inc VAT\" already includes it, so "
           "the tax on a £60 bill is £10.")),
    entry("council-tax-bands-meaning", (("council tax band", "council tax bands", "council tax valuation",
                                "valuation band"),
                               ("what", "whats", "mean", "means", "which", "check", "how")),
          ("A council tax band is the valuation bracket your home sits in, A to H in England and "
           "Scotland and A to I in Wales, and every band is a fixed fraction of band D, which is "
           "the one councils quote: about £2,171 a year in England on average, so a band B home is "
           "7/9 of that and a band H home 18/9. Check your band on the Valuation Office Agency "
           "site: if a neighbour in an identical house is in a lower band, you can ask for a "
           "review, and a "
           "quarter of a million homes have been moved down."),
          # an appeal, a challenge and a bill to bring down are how-tos, not the word
          avoid=("appeal", "appealing", "challenge", "challenging", "reduce", "lower", "wrong",
                 "how do i", "how to")),
    entry("guarantor", (("guarantor", "guarantors", "guarantor loan"),
                        ("what", "whats", "mean", "means", "need", "needs", "ask", "rent",
                         "loan", "mortgage", "risk", "do")),
          ("A guarantor is someone who signs to pay if you stop paying, so they are on the hook for "
           "the whole rent or loan, not just a month of it. Letting agents ask for one when your "
           "income is under about 30 times the monthly rent. Ask someone who could afford it and "
           "would still be talking to you afterwards, and tell them exactly what they are signing.")),
    entry("premium-bond", (("premium bond", "premium bonds", "premium savings bonds"),
                           ("what", "whats", "mean", "means", "how", "worth", "win", "wins",
                            "prize", "prizes", "rate", "return", "many")),
          ("A premium bond is a savings bond costing £1 a unit, up to £50,000, where the interest is "
           "paid out as monthly prizes instead of a rate: the prize fund is about 4% a year, but "
           "most months with a small holding you win nothing, and the smallest prize is £25. The "
           "money is safe and available, so it suits savings you might need, not ones you are "
           "counting on growing.")),
    entry("dividend", (("dividend", "dividends", "dividend yield"),
                       ("what", "whats", "mean", "means", "pay", "paid", "tax", "how", "much",
                        "yield", "get")),
          ("A dividend is the slice of its profit a company pays to shareholders, usually two to "
           "four times a year and often 2% to 4% of the share price over a year. It is not "
           "promised: a company can cut it, and a high yield is often the market saying it expects "
           "one. Outside an ISA, the first £500 of dividends a year is tax-free.")),
    # `equity` and `equities` are the same word to the matcher (an "-ies" plural folds onto its
    # "-y"), so "what is equity" was answered with the share card: the one sense, and not the one
    # most people mean. The home sense leads, the company sense follows, and `shares` stands down
    # on the word so this card answers it but the buying and selling lines stay with `shares`.
    entry("equity", (("equity", "home equity", "property equity"),
                     ("what", "whats", "mean", "means", "much", "have", "has", "own", "house",
                      "home", "property", "mortgage", "remortgage", "negative", "value", "worth",
                      "renting", "selling up")),
          ("Equity is the part you actually own. In a house it is the value minus the mortgage, so "
           "a flat worth £250,000 with £150,000 left to pay has £100,000 of equity, and it moves up "
           "and down with prices; in a company it means the shares, so equity there is a slice of "
           "the business and what it is worth."),
          avoid=("buy", "buying", "bought", "invest", "investing", "invested", "sell", "selling",
                 "sold", "shares", "share", "stock", "stocks", "market", "crash", "risky", "risk",
                 "release", "equity release", "equity loan", "lifetime mortgage", "soup"),
          bias=1),
    entry("shares", (("stock", "stocks", "share", "shares", "stock market", "share price",
                      "equities"),
                     ("what", "whats", "mean", "means", "buy", "invest", "investing", "market",
                      "how", "work", "works", "risky", "safe")),
          ("A share is a piece of a company: you get a slice of its profit and its problems, and "
           "what it is worth moves with what buyers will pay that day. One share in one company can "
           "halve; a fund holding hundreds of companies spreads that risk, which is why most people "
           "should start with an index fund inside an ISA."),
          # soup is made with stock, a flat share is a room, "share a photo" is the phone, and
          # "should i buy shares" is the how-to-invest entry's line, not a definition
          avoid=("soup", "cube", "cubes", "chicken", "vegetable", "beef", "fish", "bone", "broth",
                 "simmer", "simmering", "simmered", "boil", "boiling", "skim", "skimmed",
                 "strain", "straining", "carcass", "stockpot", "reduce", "poach", "braise",
                 "gravy", "stock pot", "recipe", "cooking", "flat share", "houseshare",
                 "house share", "room", "rent", "housemate", "share a", "share my", "share the",
                 "shares the", "share it", "share them", "screen", "screens", "folder", "file",
                 "files", "doc", "docs", "document", "documents", "photo", "photos", "picture",
                 "pictures", "album", "post", "posts", "calendar", "link", "links", "invite",
                 "location", "bills", "bill", "split", "split it", "buy", "buying", "bought",
                 "invest", "investing", "invested", "investment", "sell", "selling", "sold",
                 "market", "crash", "crashed", "safe", "risk", "risky", "worth", "should",
                 "shall", "start", "starting", "equity release", "release equity", "equity loan",
                 "lifetime mortgage")),
    entry("unit-trust", (("unit trust", "unit trusts", "investment fund", "investment trust",
                          "index fund", "fund manager"),
                         ("what", "whats", "mean", "means", "how", "work", "works", "charge",
                          "charges", "fee", "fees", "better", "worth")),
          ("A unit trust pools money from thousands of savers into one fund and you buy units worth "
           "the fund's holdings, so £100 buys a slice of everything in it. An index fund is the same "
           "idea run by a computer following a market, for under 0.3% a year, where an actively run "
           "trust charges about 0.75% and has to beat the market to be worth it.")),
    entry("fixed-rate", (("fixed rate", "fixed tariff", "fixed deal", "fixed mortgage",
                          "fixed energy"),
                         ("what", "whats", "mean", "means", "mortgage", "energy", "gas",
                          "electricity", "tariff", "deal", "worth", "how", "long", "end")),
          ("A fixed rate is a price that cannot move for a set time: a fixed energy tariff for 12 or "
           "24 months, or a fixed mortgage rate for two, five or ten years. You pay a little more "
           "than the variable rate for that certainty, and leaving a fixed mortgage early usually "
           "costs an early repayment charge, so check the exit fee before you sign."),
          bias=1,
          # This row explains what a fixed rate IS, so it asks for the question that wants the
          # definition. "is a fixed energy tariff better" is a decision and belongs to the
          # switching answer, and "should i fix my energy" to the same one; a key that mixes the
          # topic words (energy, tariff) with the ask words let a definition take both.
          ask=("what", "whats", "what is", "whats a", "mean", "means", "meaning", "define",
               "explain", "how does", "how do", "how long", "work", "works", "worth",
               "difference", "vs", "versus", "compare")),
    entry("tracker-mortgage", (("tracker", "tracker mortgage", "tracker rate", "base rate tracker"),
                               ("mortgage", "rate", "what", "whats", "mean", "means", "how",
                                "work", "works", "worth", "move")),
          ("A tracker mortgage follows the Bank of England base rate plus a fixed margin, so base "
           "4.25% with a 1% margin is 5.25%, and the payment moves the month after base changes. It "
           "is usually cheaper to leave than a fixed deal and costs less when rates fall, but the "
           "payment rises with them, so leave room in the budget for two more rises."),
          # a fitness tracker is not a mortgage
          avoid=("fitness", "watch", "wristband", "bracelet", "steps", "phone", "gym", "running")),
    # The bill itself, not the band: "what is council tax" reached nothing at all, while the band
    # row above and the how-much answer both sit on the same two words. The asks are the ones that
    # want the word explained, and every shape that wants a figure, a discount or a fight with the
    # council stands this row down so those keep their own answers.
    entry("council-tax-meaning", (("council tax", "council tax bill", "council tax charge"),
                                  ("what", "whats", "mean", "means", "explain", "why",
                                   "who", "work", "works", "actually",
                                   # "where does council tax go" and "what does council tax
                                   # pay for" were a Citizens Advice number and a savings plan:
                                   # the two words "go" and "pay for" are another row's key, and
                                   # the bill's own answer is what the services are
                                   "go", "goes", "cover", "covers", "spent", "used", "pay",
                                   "pays", "pay for", "for")),
          ("Council tax is the yearly bill your council charges on a home, not on the people in "
           "it, for the services it runs - bins, roads, libraries, social care and the fire "
           "service. What you pay is set by the band your home was put in, A to H in England and "
           "Scotland and A to I in Wales, and a band D home in England averages about £2,171 a "
           "year, so a band B home pays seven ninths of that. One adult living alone gets 25% off "
           "the bill."),
          # the figure, the band, the discount and the arrears all have their own answers
          avoid=("how much", "band", "bands", "valuation", "reduce", "lower", "discount",
                 "single person", "single occupant", "student", "students", "second home",
                 "empty", "exemption", "exempt", "arrears", "behind", "summons", "court",
                 "rise", "rises", "increase", "going up", "went up", "instalments",
                 "instalment", "refund", "rebate", "appeal", "challenge", "wrong",
                 # the rise and the letter about what is owed are their own answers
                 "go up", "goes up", "gone up", "up next year", "next year", "next april",
                 "owe", "owes", "owed", "owe more", "more than", "says i", "letter",
                 "bill says", "wrong bill", "overcharged"),
          # "what does council tax pay for" was a savings plan - the two words "pay" and "for"
          # are a money row's key - so the definition of the bill wins that line
          bias=1),
    entry("capital-gains-tax", (("capital gains", "capital gains tax", "cgt"),
                                ("what", "whats", "mean", "means", "explain", "pay", "owe",
                                 "how", "much", "rate", "rates", "work", "works")),
          ("Capital gains tax is a tax on the profit when you sell something that has gone up in "
           "value - shares, a second home, a business, a painting - not on the money the sale "
           "brings in. Your own home is exempt, and in 2025-26 the first £3,000 of gains in a year "
           "is tax free; above that, gains on shares and property are taxed at 18% or 24% "
           "depending on your income."),
          # "do i pay capital gains tax in spain" is a question about Spain, and "selling my house"
          # is the capital-gains how-to the money domain answers with the figures
          avoid=("spain", "france", "portugal", "italy", "abroad", "overseas", "america",
                 "usa", "australia", "canada", "ireland", "sell my house", "selling my house",
                 "sell my flat", "selling my flat", "my main home", "gift", "gifting",
                 "inheritance")),
    # "what is a union" and "what does a trade union do" were both shrugs, and a union is a word
    # people meet on a payslip line and a contract. The union of two countries, the Union Jack and
    # a students' union are other things, so those stand this row down.
    entry("trade-union", (("trade union", "trade unions", "union rep", "union representative",
                           "union member", "union membership", "a union", "unions"),
                          ("what", "whats", "mean", "means", "does", "do", "explain", "for",
                           "how", "work", "works", "actually")),
          ("A trade union is a body of workers in the same job or industry that bargains with "
           "employers over pay, hours and safety, and it can take a case to an employment tribunal "
           "on your behalf. You pay a monthly subscription, often around 1% of pay or a few pounds "
           "a week, and what most people join for is the legal cover: a rep beside you in a "
           "disciplinary or a redundancy, which your employer has to allow."),
          avoid=("soviet", "ussr", "russia", "european union", "brexit", "eu", "union jack",
                 "jack", "flag", "rugby", "football", "credit union", "student union",
                 "students union", "students' union", "station", "train", "rail", "workhouse",
                 # a union question with a dispute in it is not a definition: "can i be sacked
                 # for joining a union" had the rep's answer and was given the word instead, and
                 # "which union is best for teachers" is a choice between two of them
                 "sacked", "sack", "sacking", "dismissed", "dismissal", "fired", "tribunal",
                 "redundancy", "redundant", "strike", "strikes", "striking", "ballot",
                 "best union", "which union", "join a union", "joining a union", "joining",
                 "subscription", "subs", "fees")),
    entry("debit-card", (("debit card", "debit cards", "a debit"),
                         ("what", "whats", "mean", "means", "work", "works", "how",
                          "difference", "different", "vs", "versus", "explain")),
          ("A debit card takes the money straight out of your own account as you pay, so you can "
           "only spend what is there; a credit card borrows from the card company and sends you a "
           "bill later, with interest if you do not clear it. A debit card costs nothing to use "
           "and cannot leave you in debt, while a credit card over £100 gives you the card "
           "company's protection if the seller goes bust or never delivers."),
          # a card that was declined, charged twice or used fraudulently is a complaint with its
          # own answer, and so is opening an account to get one
          avoid=("declined", "decline", "charged twice", "double charged", "fraud", "fraudulent",
                 "stolen", "lost", "scam", "refund", "chargeback", "contactless", "fees",
                 "fee", "abroad", "travel", "open an account", "switch", "cashback", "pin")),
    entry("escrow", (("escrow", "in escrow", "escrow account"),
                     ("what", "whats", "mean", "means", "work", "works", "how", "explain",
                      "why", "money", "held")),
          ("Escrow is money held by a third party until both sides have done what they promised. "
           "In a house purchase your deposit sits with your solicitor until completion, and if the "
           "sale falls through it comes back to you; on a building job a stage payment can sit in "
           "escrow until the work is signed off. Nobody in the middle can spend it, which is the "
           "whole point."),
          avoid=("how do i", "should i", "worth it")),
    entry("deductible", (("deductible", "deductibles", "insurance deductible", "an excess",
                          "policy excess", "insurance excess"),
                         ("what", "whats", "mean", "means", "how", "much", "work", "works",
                          "explain", "difference", "pay")),
          ("The deductible, which in the UK is usually called the excess, is the first part of a "
           "claim you pay yourself: with a £250 excess on a £900 repair the insurer pays £650. "
           "A higher excess lowers the premium, so work out what you could actually find in a bad "
           "month before choosing one. Windscreen cover usually has a much smaller separate "
           "excess, often £75."),
          avoid=("how do i", "should i", "worth it")),
    entry("agreement-in-principle",
          (("mortgage in principle", "agreement in principle", "decision in principle",
            "mortgage promise", "dip", "aip"),
           ("what", "whats", "mean", "means", "how", "long", "worth", "need", "get", "explain",
            "does it", "last")),
          ("A mortgage in principle, also called an agreement or decision in principle, is a "
           "lender's written 'we would lend you about this much' before you have found a house. It "
           "is based on a soft credit check and your income, it usually lasts 60 to 90 days, and "
           "estate agents ask for it because it shows you can actually buy. It is not an offer and "
           "not a guarantee: the full application checks the property and the paperwork, and the "
           "amount can come out lower. Get one before you start viewing and keep the figure you "
           "really need in mind, not the top one."),
          avoid=("how do i", "should i", "worth it", "apply")),
    entry("pawn-shop", (("pawn shop", "pawnshop", "pawnbroker", "pawn broker", "pawn brokers",
                        "pawnbrokers", "cash converter", "cash converters"),
                       ("what", "whats", "mean", "means", "how", "work", "works", "explain",
                        "much", "borrow", "sell", "interest", "get back", "lose")),
          ("A pawn shop, or pawnbroker, lends you money against something you leave with them - "
           "jewellery, a watch, a musical instrument - and holds it until you pay back the loan "
           "plus interest, usually 5% to 10% a month; if you do not, they sell it. You get far "
           "less than the item is worth, so it is a short-term fix rather than a way to raise "
           "money: a credit union loan or a free debt adviser such as StepChange costs much less "
           "if you can wait a few days."),
          avoid=("how do i", "should i", "worth it")),
    # Four words that a person meets in a contract or on a forecourt and had no card for at all
    # ("what is hire purchase", "what is a bridging loan", "what is equity release" and "what is a
    # charge on a house" all met the search hedge), and a fifth whose sense the property table
    # skipped because a bare "service charge" is a restaurant's. Each is a word to explain, so the
    # domain's NOT_A_DEFINITION fence below applies to them the same way.
    entry("hire-purchase", (("hire purchase", "hire-purchase", "hp agreement", "car finance"),
                            ("what", "whats", "mean", "means", "explain", "work", "works",
                             "how", "difference", "better", "own", "owe", "cancel", "return")),
          ("Hire purchase is paying for something in instalments while you use it: the lender owns "
           "it until the last payment, then it is yours. Most forecourt car finance is this. You "
           "can hand the car back once you have paid half of the total, and the rate is fixed, but "
           "you cannot sell it before the end without settling it first."),
          # a fault with the car, the repayments and the dealer are other cards' lines
          avoid=("broken", "fault", "engine", "mot", "repayment", "repayments", "missed",
                 "miss a payment", "afford", "dealer", "complaint", "warranty", "deposit")),
    entry("bridging-loan", (("bridging loan", "bridging loans", "bridging finance", "bridge loan"),
                            ("what", "whats", "mean", "means", "explain", "work", "works",
                             "how", "much", "cost", "need", "worth", "alternative")),
          ("A bridging loan is short-term money to buy a place before the old one sells: 0.5% to "
           "1% a month rather than a year, so £150,000 over six months costs several thousand in "
           "interest and fees. It keeps a chain together when the sale is certain, and the lender "
           "wants a dated exit - a sale or a mortgage - so it is the wrong money for a house that "
           "is not selling."),
          bias=1),
    entry("equity-release", (("equity release", "lifetime mortgage", "home reversion",
                              "release equity", "release money from my house"),
                             ("what", "whats", "mean", "means", "explain", "work", "works",
                              "how", "much", "cost", "worth", "should i", "risks", "catch")),
          ("Equity release takes money out of a home you own without moving: a lifetime mortgage "
           "adds the interest to the loan, so the debt grows, and a home reversion sells a share "
           "of the house outright at below market value. Nothing is repaid until you die or go "
           "into care, which is why the family inherits less. Take advice from someone who does "
           "not sell them - it is free and it is required."),
          bias=1),
    entry("charge-on-a-house", (("charge on the house", "charge on my house", "charge on a house",
                                 "charge on the property", "a charge", "charging order"),
                                ("what", "whats", "mean", "means", "explain", "removed",
                                 "remove", "lift", "sell", "mortgage", "land registry")),
          ("A charge on a house is a note on the title that someone's money is secured on it, so "
           "it cannot be sold or remortgaged without paying them. A mortgage is a charge, and so "
           "is a secured loan or a charging order after a debt went to court. It comes off the "
           "title when the debt is cleared, and the Land Registry shows who holds it."),
          # a criminal charge, and a charge for a service or a bag, are other cards' lines
          avoid=("criminal", "police", "court date", "accused", "service charge", "no charge",
                 "free of charge", "charged me", "carrier bag", "extra charge")),
    entry("sinking-fund", (("sinking fund", "sinking funds", "a fund for repairs",
                            "savings for repairs", "maintenance fund"),
                           ("what", "whats", "mean", "means", "explain", "how", "much",
                            "set up", "start", "work", "works", "need")),
          ("A sinking fund is money set aside a little at a time for a cost you know is coming: "
           "£50 a month for a roof, a boiler or a car's tyres. Work out the bill and the years, "
           "divide, and keep it in a separate easy-access account so it is not spent. It is the "
           "same idea a leaseholder's building fund uses, and it is why a repair is a plan rather "
           "than a shock."),
          bias=1),
    entry("help-to-buy-isa", (("help to buy isa", "help-to-buy isa", "htb isa",
                               "help to buy savings"),
                              ("what", "whats", "mean", "means", "explain", "still", "open",
                               "use", "bonus", "worth", "closed", "claim")),
          ("A Help to Buy ISA was the first-home savings account that added 25% on what you saved, "
           "up to £3,000, when the money went on a first home under £250,000 (£450,000 in London). "
           "It closed to new savers in November 2019, but an existing one can still be paid into "
           "until November 2029 and claimed until 2030. The Lifetime ISA is the one open now."),
          bias=1),
]

# A how-to or a decision is not a word to explain. "how do i pay my self assessment" had the
# filing answer and was given the definition instead, "how do i claim vat back" a definition for a
# question about reclaiming, and "should i get a tracker mortgage" a definition for a choice: the
# word's entry is only an answer when the line is asking what the word means or how it works, so
# every entry in this domain stands down on the shapes that ask for something to be done. The
# cases that stay are the ones the word really answers: "what is X", "what does X mean", "explain
# X", "how does X work", "how much is X", "is a monthly or annual one better".
NOT_A_DEFINITION = ("how do i", "how can i", "how to", "should i", "is it worth", "worth it",
                    "what should i do", "help me", "what can i do about",
                    # a job to do is not a word to explain: "my council tax bill says i owe
                    # more than i thought, what can i do" had the ring-the-council answer, and
                    # "what do i ask them to check" the breakdown, and both were handed the
                    # definition of the bill. "remind me" and "dont let me forget" are the
                    # memory rows' lines, not the word's.
                    "what can i do", "what do i do", "what do i ask", "what to ask",
                    "who do i ask", "remind", "reminds", "reminder", "forget", "forgot",
                    "remember to", "dont let me")
for _item in ENTRIES:
    _item.avoid = _item.avoid + NOT_A_DEFINITION

ANSWERS = ("money",)
