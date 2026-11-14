# Split application and registration

The code used one concept, "registration", for two different things: a student's application to a course (the answers the teachers need for team assignment) and the student's place in a semester (course and teams). An unfinished rework added a second, question-based model alongside the old one without connecting the two, which broke team assignment and the user admin. We decided to keep two separate concepts. The **application** lives in its own `applications` app, with a question-based **application form** per semester. The **registration** is the old `Registration` model, slimmed down to student, semester, course and teams. Importing the team assignment creates the registration from the application.

## Considered options

- **One model for both.** This was rejected because application answers have no role once teams are assigned, while the registration is used all semester long by teams, GitHub sync, mailing lists, questionnaires and room reservations.
- **Put everything in the new question-based model and drop the old one.** This was rejected because all production data and every feature outside the sign-up already use the old `Registration`, and the new tables had never been deployed.
- **Share one application form across semesters.** This was rejected in favour of copying the form for each semester. Changing a question for next year must never change how earlier answers read, and those answers must be kept for several years in case of grade disputes.
- **Export the old application answers to a file.** This was rejected in favour of converting them into applications, so that old and new data sit in one place behind the same admin filters.

## Consequences

- Moving the new models into their own app and replacing their migration was cheap only because their tables had never reached production.
- Each application form lists the courses that can be applied for, and questions can be limited to particular courses. The student chooses their course before filling in the form, and the course is a field of the application rather than a question.
- Questions are edited only on their own form's admin page, so the copies made for each semester do not clutter a shared list. Deleting a question or choice that has answers is blocked.
- For now a student has one registration per semester that can hold several teams. One registration per team may follow later. Moving to it costs about the same later as it would now, because production already holds registrations with several teams.
- Old application answers are converted only for spring semesters. A fixed table records the semester in which each old field was introduced, so that values stored only as defaults do not become answers. Fall answers are dropped. After the conversion the old fields, and the unused automatic team assignment that relied on them, are removed.
