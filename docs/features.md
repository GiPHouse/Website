# Features

What the website does and how its main parts work.

- [Authentication and Users](#authentication-and-users)
- [GitHub OAuth](#github-oauth)
  - [Creating Admin Users](#creating-admin-users)
- [Semesters](#semesters)
- [Registrations](#registrations)
  - [Automatic team creation](#automatic-team-creation)
- [Questionnaires](#questionnaires)
- [Room Reservations](#room-reservations)
- [Course, Project and Static Information](#course-project-and-static-information)
- [Projects and Repositories](#projects-and-repositories)
  - [GitHub Synchronization](#github-synchronization)
- [Mailing Lists](#mailing-lists)
- [Tasks](#tasks)
- [Styling](#styling)

## Authentication and Users
Because every student needs to have an GitHub account to participate in the GiPHouse courses, authentication is based on GitHub OAuth. This removes the need to save separate usernames and passwords. Instead of usernames and passwords, the website uses GitHub IDs to authenticate users.

A [custom user model](https://docs.djangoproject.com/en/dev/topics/auth/customizing/#using-a-custom-user-model-when-starting-a-project) (called `Employee`) has been created to make this possible.

## GitHub OAuth
The website has single click login because it uses [GitHub's OAuth implementation](https://developer.github.com/apps/building-oauth-apps/authorizing-oauth-apps/).

The GiPHouse GitHub organization has a GitHub App set up which is used for both repository synchronisation (see [Projects and Repositories](#projects-and-repositories)) and GitHub OAuth, which allows users to authorize the GiPHouse GitHub organization to see (limited) information about them. This App has credentials (a client ID and a client secret key), which are loaded into the Django settings using environment variables.

The authentication flow is as follows.
1. A user requests to login or register.
2. The user is redirected to `https://github.com/login/oauth/authorize`.
3. If the user has not authorized the GiPHouse GitHuB (OAuth) App, GitHub asks the user to do so.
4. If the user has authorized the GiPHouse Github (OAuth) App, they are redirected to the GiPHouse website with a temporary code as GET parameter.
5. The website uses this code to request an access token from the GitHub API.
6. The website uses the access token to request information about the user.

To support this authentication flow, [a custom authentication backend](https://docs.djangoproject.com/en/dev/topics/auth/customizing/) (called `GithubOAuthBackend`) has been created.

### Creating Admin Users
Admin users (i.e. teacher, director or student assistant) do not have to register, they need to be created manually. In the backend it is possible to add new users. Every user should have their GitHub ID and GitHub username set. To promote a user to superuser, they should have the "Staff status", "Active" and "Superuser status" checkboxes checked.

## Semesters
The website makes the distinction between the spring semester (February - August) and the fall semester (September - January). Most of the content on the site is split by semester and year, because the content of the course that are given in the spring semester generally have nothing to do with the courses of the fall semester.

## Registrations
Every semester has a registration start and end date. Users will be able to between the start and end of the registration. They can do this by going to [https://giphouse.nl/register/](https://giphouse.nl/register/).

The registration process consists of two steps:
1. Authorizing the GiPHouse GitHub (OAuth) App.
2. A form that asks question about the registration (e.g. email, student number and project preferences).

The questions for the registration can be dynamically generated and any new questions will appear on the form in the front end. We do make use of "labels" for every question so they can be accounted for in the back end. Questions should thus be properly labeled whenever possible. Non-labeled questions will be added as an additional column in the csv export but will not be considered for the SAT solver.

There is an option to create a sample registration with the most important questions listed and labeled. The labels here should be appropriate already but the wording of the questions and the choices for the questions can be changed.

The project and partner preference is not required. They can be left open if people do not have any preferences. The amount of possible partner and project preferences can be adjusted by using the CHOICELIST and TEXTLIST and then adjusting the amount of max_choices in the admin. 

If multiple semesters have open registrations at one moment, the chronologically newest semester is picked. For example, if the fall 2019 and spring 2020 semester both allow registrations at one moment, users will register for the spring 2020 semester (even if at the moment of registration it is officially fall 2019).

It is possible for users to register multiple times. For example, if a user wants to follow a course in the fall semester and a different course in the spring semester. However, users cannot register multiple times within the same semester.

There is no built-in support for directors (which will look like registrations that are not appointed to a project).

### Automatic team creation
Admin users can generate a suggested team assignment.
This suggested team assignment is generated by solving a linear integer optimization and constraint satisfaction problem using [Google OR-Tools](https://github.com/google/or-tools).

The constraint satisfaction problem is based on the [nurse scheduling problem](https://developers.google.com/optimization/scheduling/employee_scheduling). It contains constraints that ensure that:
- Everyone is assigned to exactly one project.
- Managers and engineers are distributed equally over all projects.
- All projects contain at least one dutch speaking manager. This constraint is left out if there are fewer dutch speaking managers than there are projects.

In addition to these constraints it contains objectives that are tried to be met, but not guaranteed:
- Employees should be in one of their preferred projects. The first project preference is preferred over the second.
- Employees should be in the same projects as their partner preferences. The order of the partner preferences does not matter for this.
- Projects should contain employees with varied programming experience.

## Questionnaires
During the courses, the students need to fill out surveys about the course, their project progress and their team. Admin users are able to create questionnaires and view submission by students in the backend. 

The questions in the questionnaires are of the following types:
1. Poor/good likert scale,
2. Disagree/agree likert scale and
3. Open question.

It is also possible to ask a question multiple times about each teammate. 

Questionnaires have a soft deadline and a hard deadline, which allows students to submit their answers late (i.e. after the soft deadline but before the hard deadline).

## Room Reservations
The room reservation is built using [FullCalendar](https://fullcalendar.io/), a popular JavaScript Calendar. FullCalendar allows users to drag rooms that they want to reserve into timeslots. FullCalendar makes requests to the website to save changes in the database. The rooms are created in the backend by admin users.

## Course, Project and Static Information
Admin users can add information about the course lectures and the projects in the backend. There are also a small amount of static HTML webpages with information about GiPHouse.

## Projects and Repositories
The projects module provides synchronisation functionality with a GitHub organization using the [GitHub API v3](https://developer.github.com/v3/). For this, a repository model is included in Django. Project(team)s can have one or multiple repositories, which are then synchronised with GitHub. For this functionality, a [GitHub App](https://developer.github.com/v3/apps/) must be registered and installed in the organization. Setting one up is explained in [GitHub App and G Suite setup](integrations.md).

### GitHub Synchronization
Projects and repositories contain a field `github_team_id` and `github_repo_id` that corresponds to the respective `id` of the object on GitHub. The `github_team_id` field is automatically set and should not be touched under normal circumstances. For repositories, one can choose to:

- To create a new repository, which can be done in two ways:
	- Automatically, by selecting "Create default repository" which will fill the details for the user,
	- Manually, where the user can specify the name and privacy settings;
- To link an existing repository by selecting the respective option and specifying its `id`, which will again fetch details and fill them for the user.

Teams and repositories on GitHub that do not match these id's will not be touched by the GitHub synchronization. 
If the `github_team_id` or `github_repo_id` are `None`, it is assumed the objects do not exist and new objects will be created on synchronization (except for archived projects and teams).

Repositories and project(team)s are synchronized with GitHub in the following manner:

- For each project, a GitHub Team is created in the organization.
    - Employees of a project are added to the team as "member"s.
    - All users (employee or not) that do not belong in a team, are removed from both the team and the organization.
    - Organization owners will never be removed from the organization, only from the team.
    - Teams that are manually created in GitHub and not linked in Django, are ignored and will not be removed.
- Each repository is created on GitHub in the organization.
    - Depending on the environment variables, either a private or public repository is created.
    - The associated team is given "admin" access to the repository.
    - Other additional permissions of a repository stay untouched.
- Repositories can be archived.
    - Repositories that are marked as 'To be archived' will be archived on GitHub during the next sync. After they have been archived on GitHub, they are marked as 'Archived' and can only be unarchived manually via [github.com](). 
    - A project is considered archived if all of its repositories are archived.
    - If a project is archived, the associated GitHub Team will be removed and consequently, all employees will be removed from the organization (again, organization owners are ignored).    

Synchronization is automatically triggered by every meaningful change done to a project (for changes in repositories, in employees, etc). 
Superusers can manually initialize the synchronization for either a number of specific projects or for every project of the current semester. This is done via actions on specific sets of objects in their changelists, or via the big 'synchronize to GitHub' button (to perform synchronization on all objects) in the admin. Synchronization is implemented in a [idempotent](https://en.wikipedia.org/wiki/Idempotence) manner. 

Synchronization currently does not regard the role of directors of GipHouse. This needs to be configured manually. Note that it is however not possible to add directors manually to a team on GitHub, since they will be removed after each sync.

## Mailing Lists
Admin users can create mailing lists using the Django admin interface. A mailing list can be connected to projects, users and 'extra' email addresses that are not tied to a user. Relating a mailing list to a project implicitly makes the members of that project a member of the mailing list. Removing a mailing list in the Django admin will result in the corresponding mailing list to be archived or deleted in G suite during the next synchronization, respecting the 'archive instead of delete' property of the deleted mailing list. To sync a mailing list with G Suite, one can run the management command: `./manage.py sync_mailing_list` or use the button in the model admin. This will sync all mailing lists and the automatic lists into G Suite at the specified domain.

This sync starts by creating groups in G Suite for all mailing lists currently not in there, after they are created a request is done per member of that group to add them to the group. For the already existing groups a list is made of existing members in the group and the needed inserts or deletes are done to update the group.

## Tasks
A task is a process that takes more time than can fit in a request. The process is run in a separate thread and the status is synced to the task. The task is then used to show the user the progress and whether something has gone wrong in form of an error log.

## Styling
[Bootstrap](https://getbootstrap.com/) and [Font Awesome](https://fontawesome.com/) are used to style the website. Their respective SCSS versions are used.
