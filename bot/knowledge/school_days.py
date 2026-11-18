"""A day cut out of school: the office, the note, the lesson that will be missed.

One question whoever types it, so it is keyed on the day and the appointment rather than on
whether a pupil or a parent is asking. It lives in its own file rather than in `study.py`
because that file is edited by several lanes at once and a row added in the middle of it is the
first thing a rebase takes away; a domain file that exists only for this question costs nothing
and cannot collide.

"""

from .lookup import entry

ANSWERS = ("school-and-study",)

ENTRIES = []

# A day cut out of school is arranged with the office, and every way people type it was answered
# by something else on main: "how do i ask to leave school early" was a hedge, "i need to leave
# school early today" was the composer's "what's stopped it happening so far", "my son needs to
# leave school early for a dentist appointment" was the card for finding an NHS dentist, and
# "im leaving school early today" was told not to tell a boss until there is an offer in hand -
# the words "im leaving", read as a resignation. It is one question whoever is asking it, so it is
# keyed on the day and the appointment rather than on whether a pupil or a parent is typing.
ENTRIES.append(entry(
    "school-leaving-early",
    (("leave school early", "leaving school early", "left school early", "leave early from school",
      "leaving early from school", "out of school early", "out of school for",
      "leave class early", "leaving class early", "leave a lesson early",
      "leave school before the end", "finish school early", "school finish early",
      "early from school", "sign out of school", "sign them out", "sign him out", "sign her out",
      "collect my child early", "collect her early", "collect him early", "collect them early",
      "pick my child up early", "pick my son up early", "pick my daughter up early",
      "leave college early", "leaving college early", "leave uni early", "leaving uni early",
      "take my son out of school", "take my daughter out of school",
      "take my child out of school", "take him out of school", "take her out of school",
      "appointment in school time", "appointment during school", "dentist in school time",
      "dentist appointment school", "during school hours"),
     ("school", "class", "lesson", "period", "pupil", "teacher", "form tutor", "office",
      "reception", "head of year", "child", "son", "daughter", "kid", "kids", "early", "earlier",
      "today", "tomorrow", "afternoon", "morning", "appointment", "dentist", "doctor", "hospital",
      "clinic", "note", "email", "permission", "authorised", "authorized", "attendance")),
    ("Ask the school office in advance and put it in writing: a note or an email naming the day, "
     "the time and who is collecting is enough for an appointment, and the office logs it as "
     "authorised absence. A pupil who leaves on their own should tell their form tutor and the "
     "teacher whose lesson they will miss, so nobody marks them absent, and take the work with "
     "them. Ring the office the same morning only for something you could not plan, and read the "
     "attendance policy before anything that is not medical - an appointment, a funeral and a "
     "religious day are authorised, a family trip in term time usually is not, and repeated "
     "unauthorised absence is what leads to a fine."),
    bias=1,
    # a school and a child have to be named: "how do i leave early from work" is the work row, and
    # "i left early" on its own is not a school question whatever the day held
    ask=("school", "class", "lesson", "pupil", "teacher", "form tutor", "college", "uni",
         "sixth form", "son", "daughter", "child", "kid"),
    # the sick child, the child who will not go, and the holiday dates are their own rows
    avoid=("off school", "stay off school", "keep him home", "keep her home", "keep them home",
           "keep my child home", "well enough", "temperature", "fever", "sick", "vomiting",
           "diarrhoea", "refuses to go", "refusing to go", "wont go", "won't go", "hates",
           "hate", "bully", "bullied", "bullying", "breaks up", "break up", "term dates",
           "term starts", "go back", "holidays", "half term", "inset day", "school uniform",
           "nursery", "childminder", "homework", "exam", "revision",
           # leaving for good is not a day out of school: "im leaving school next summer" and
           # "i leave school at the end of term" are the school-leaver questions
           "next year", "next summer", "next term", "for good", "at the end of", "school leaver",
           "sixth form", "leaving school soon", "when i leave",
           # "leave school early" is two questions in one phrase: the day out and the end of
           # school. "i want to leave school early and get a job" is the leaving-at-16 question,
           # and a note about a dentist at 2pm is the wrong answer to it, so a stated job or a
           # stated leaving of education stands this row down. "a job" on its own stays out of
           # the list: leaving early *for a job interview* is an appointment like the dentist's.
           "get a job", "got a job", "and get a job", "a full time job", "career", "careers",
           "apprenticeship", "apprenticeships", "a levels", "a level", "qualifications",
           "at 16", "sixteen", "drop out", "dropping out", "quit school", "quitting school",
           "leave at 16", "leaving at 16", "finish school at 16", "not going back",
           "wont be going back", "won't be going back")))
