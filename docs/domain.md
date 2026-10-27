# Domain

How GiPHouse and its courses are organised, and how the website is used for them. Terms in **bold** are defined in the [glossary](../GLOSSARY.md). This document describes the situation as it is; it is not a plan for changing the code.

## Courses

GiPHouse runs three courses, split over two semesters:

- **Spring**: Software Engineering (SE) and System Development Management (SDM) run together. Engineers (SE) and managers (SDM) are combined into teams, and each team works on a project for a client.
- **Fall**: Software Development Entrepreneurship (SDE). Entrepreneurs form teams that pick their own product idea and start a small business around it. There are no clients and no projects.

All three courses use the website. The website is, however, heavily optimised for SE and SDM; see [current inconsistencies](#current-inconsistencies).

A student follows at most one course per semester, so it is not possible to follow SE and SDM in the same spring. A student may follow the same course again in a later year, for example to retake it.

## Users and access

Anyone with an account is a **user**. Students, directors and teachers are all users. Teachers and directors both work in the website's backend. Where needed they can be given restricted administrator rights; there is no further distinction by director position.

## Organisation

GiPHouse simulates a company:

- The **teachers** form the Supervisory Board. They are responsible for the course material and grading.
- The **directors** form the Executive Board. They are student assistants who run GiPHouse day to day, and every teaching assistant is a director.
- **Managers** (SDM students) lead the project teams.
- **Engineers** (SE students) do the development work.

## Applying and registering

A student who wants to follow a course in a semester submits an **application**. The application carries the information the teachers need to place the student in a team, such as experience, preferences and availability. Which questions are asked differs per semester and course. The application exists to inform team assignment and has no purpose after that.

When the teachers and teaching assistants accept an application, which in practice happens at team assignment, a **registration** is created. It links the student to the semester, their course and their team(s). Rejecting an application is rare: the student is simply not placed in a team, and their account may be deleted. Students who withdraw keep a registration but no team, and no separate concept is needed for them.

A student can be in more than one team in a semester. In practice this means managers who lead several teams. A student could also switch teams mid-semester; their questionnaire peer questions should then cover the members of both teams. Whether such a student has one registration with several teams or a separate registration per team is an open design question.

## Team assignment

Teams are no longer assigned automatically by the website. The current, work-in-progress workflow is:

1. Students apply through the website.
2. The applications are exported to CSV.
3. The teachers make the team assignment outside the website, using their own scripts and human judgement. `smt_solver_gip/` is an example of such a script: it reads the exported CSV and helps a teacher build an assignment interactively. It is independent of the website's own automatic assignment and has never been used together with it.
4. The resulting assignment is imported back into the website as CSV.

## During the semester

- **Questionnaires** are used in all courses.
- **Room reservations** are used in all courses. Any student with a registration in the current semester can reserve a room, and so can teachers and directors.
- **Mailing lists** are mostly managed by the directors. The directors' own list is managed by hand.
- **Lectures** (course content and lecture sign-ups) are no longer used.

## Current inconsistencies

Places where the code (or its documentation) does not match how the courses currently work.

- **Directors.** The code treats a director as "an SDM registration with no project" (`is_director` in `website/registrations/models/registration.py`), and `docs/features.md` describes directors in the same way. That setup was used until around 2021. Directors are now student assistants and are not SDM students.
- **Employee.** The code calls every user an `Employee`, including teachers and other admins. In the domain, people are **users**, and the people following a course are **students**.
- **SDE support.** The website is built mostly around SE and SDM (for example engineers and managers, client projects and management interest), and supports SDE poorly. Where the code treats entrepreneurs at all, it treats them roughly like engineers.
- **Team versus project.** The code has no separate notion of a team: the `Project` model is both the client's assignment and the group of students, and the GitHub team, repositories and mailing lists hang off it. SDE teams are therefore stored as projects without a client.
- **Application versus registration.** The code calls the sign-up form a "registration", but filling it in is really an application. Creating an account is also tied to that form: the only way to get an account is to apply for a semester. As a result, a student who already followed SE has a confusing time applying for SDE later. Teachers and directors also have to be added by hand, instead of getting staff status on an account they created themselves.
- **Application data kept on the registration.** Because one model covers both concepts, a registration carries all the application answers (experience, preferences, availability and so on) long after team assignment, where they are no longer relevant. The in-progress code was meant to start separating them.
- **Course not checked against the semester.** Nothing stops a registration for a course that does not run in that semester. The production data has SE and SDM registrations in fall semesters, inside SDE teams. These come from students choosing the wrong course on the single form, or from registrations copied by hand from an earlier semester without the course being changed (students who already had an account did not apply properly).
- **Two registration models.** The code holds an older `Registration` model with fixed fields and a newer, question-based `Registrations`/`RegistrationSubmission` model side by side.
- **Administrator rights.** In practice almost all staff users are superusers, while the intent is that they get only the rights they need.
- **Room reservation access.** The code lets any logged-in user reserve rooms, including students from earlier semesters. Only students with a registration in the current semester, teachers and directors should be able to.
- **Client contact person.** A client can have a contact person, but the code only stores a client's name and logo.
- **Lectures.** The lecture and lecture-sign-up features are still in the code and on the website, but are no longer used.
- **Spring 2024 data.** In the production data, all spring 2024 registrations lack a project, apparently because that semester's projects were deleted while the registrations remained.
- **Automatic team assignment.** The automatic team assignment in `website/registrations/team_assignment.py` and its description in `docs/features.md` are no longer used: its results needed so many manual corrections that teams are now assigned by hand (see [Team assignment](#team-assignment)).
