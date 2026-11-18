"""The first day at secondary school: a school year is not a length of time.

The answers lane owns this domain. It is one question, asked over and over in the last week of
August by a parent who has just been told which form their child is in: what do I send them with.

Both rows that used to answer it were answering a different question. The gone-quiet row is keyed
on "in years", the length of time a silence is measured in, and the matcher folds inflections, so
"my daughter is in year 7, what should she take on her first day" reached "A relative going quiet
is usually nothing more than a busy year". The weaning card is keyed on a child's words plus
"first", so "what should my son take on his first day at secondary school" reached "Start with
soft food they can hold themselves".

A school year is a phrase in its own right here - "year 7" to "year 11", "first day of year 8",
"starting secondary", "big school" - so the row reaches the same line the gone-quiet row reaches
and scores higher on the day itself, rather than standing another row down.

Everything else about a child that age already has a good answer and keeps it: the school's
uniform list, whether they need a phone, packed lunch ideas, being nervous about the change, and
what time the day starts. Each of those is fenced out of this row by name.
"""

from .lookup import entry

ANSWERS = ("family-and-parenting", "school-and-study")

ENTRIES = [
entry(
    "secondary-first-day-kit",
    (("first day at school", "first day at secondary", "first day at big school",
      "first day of year 7", "first day of year 8", "first day of year 9", "first day in year 7",
      "first day in year 8", "first day in year 9", "starting year 7", "starting year 8",
      "starting year 9", "starting year 10", "starts year 7", "starts year 8", "starts year 10",
      "starting secondary", "starts secondary", "starting high school", "starts high school",
      "starting big school", "starts big school", "new school", "year 7", "year 8", "year 9",
      "year 10", "year 11", "yr 7", "yr 8", "yr 9", "yr 10",
      "secondary school", "high school", "big school"),
     ("take", "bring", "pack", "put in", "need", "buy", "get", "kit", "equipment", "bag",
      "rucksack", "wear", "first", "day", "start")),
    ("Nothing fancy for the first day: a named bag with a pencil case (two pens, a pencil, a "
     "rubber, a ruler), a water bottle, a packed lunch or the money loaded on the dinner account, "
     "and the PE kit the school asked for, in a bag of its own if they can. Label everything, "
     "including the coat and the shoes, and put the timetable in the front pocket. Buy the cheap "
     "version of each until the school sends its list, then fill the gaps."),
    avoid=("baby", "weaning", "puree", "pureed", "milk", "bottle", "breast", "formula",
           "solids", "teething", "nursery", "reception", "first birthday", "first tooth",
           # a phone, a laptop and the uniform list are their own questions about the same year
           "phone", "mobile", "smartphone", "ipad", "tablet", "laptop", "console",
           # a shopping list for the year is the school's-list card's question, which answers it
           # with the badge jumpers and the two pairs of trousers
           "uniform", "list", "buy", "buying", "prices", "price", "how much", "cost",
           # being nervous about the change is its own answer, and so is the school day's shape
           "nervous", "worried", "worry", "scared", "anxious", "anxiety", "settle", "settling",
           "cope", "coping", "make friends", "friends", "bully", "bullied", "what time",
           "times", "hours", "bus", "route", "walk to school", "term dates", "holidays",
           "first word", "first steps", "first day at work", "first day in the job",
           "new job", "back at work", "interview", "leaving", "left", "return to work",
           "gone quiet", "hasnt called", "wont talk", "not speaking"),
    ask=("what", "need", "take", "should", "do i", "first day", "starting", "starts"),
    bias=2),
]
