# GiPHouse website

![](https://github.com/giphouse/Website/workflows/Linting%20and%20Testing/badge.svg) ![](https://github.com/giphouse/Website/workflows/Deploy%20to%20production/badge.svg) [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black) ![](https://img.shields.io/badge/coverage-100%25-brightgreen)

This is the code for the website of [GiPHouse](http://giphouse.nl/) powered by [Django](https://www.djangoproject.com/).

## Table of Contents
- [GiPHouse website](#giphouse-website)
  - [Table of Contents](#table-of-contents)
  - [Features](#features)
    - [Authentication and Users](#authentication-and-users)
    - [GitHub OAuth](#github-oauth)
      - [Creating Admin Users](#creating-admin-users)
    - [Semesters](#semesters)
    - [Registrations](#registrations)
      - [Automatic team creation](#automatic-team-creation)
    - [Questionnaires](#questionnaires)
    - [Room Reservations](#room-reservations)
    - [Course, Project and Static Information](#course-project-and-static-information)
    - [Projects, Repositories and AWS](#projects-repositories-and-aws)
      - [GitHub Synchronization](#github-synchronization)
      - [AWS Synchronization](#aws-synchronization)
    - [Mailing Lists](#mailing-lists)
    - [Tasks](#tasks)
    - [Styling](#styling)
  - [Development and Contributing](#development-and-contributing)
    - [Getting Started](#getting-started)
      - [Logging into the Backend](#logging-into-the-backend)
      - [Registering a GitHub App for repository synchronisation](#registering-a-github-app-for-repository-synchronisation)
      - [Registering a G Suite service account for mailing list synchronisation](#registering-a-g-suite-service-account-for-mailing-list-synchronisation)
      - [Registering an AWS environment for synchronisation](#registering-an-aws-environment-for-synchronisation)
    - [Dependency Management](#dependency-management)
    - [Fixtures](#fixtures)
    - [Tests](#tests)
    - [Code quality](#code-quality)
  - [Deployment](#deployment)
    - [Docker](#docker)
      - [Dockerfile](#dockerfile)
      - [Entrypoint](#entrypoint)
      - [GitHub Packages](#github-packages)
      - [Docker Compose](#docker-compose)
        - [`nginx`](#nginx)
        - [`letsencrypt`](#letsencrypt)
        - [`postgres`](#postgres)
        - [`web`](#web)
    - [Deployment Pipeline](#deployment-pipeline)
      - [`deploy.yaml` workflow](#deployyaml-workflow)
        - [`build-docker` job](#build-docker-job)
        - [`deploy` job](#deploy-job)
      - [Secrets](#secrets)
    - [Server Configuration](#server-configuration)
    - [Keeping Everything Up to Date](#keeping-everything-up-to-date)

## Features

### Authentication and Users
Because every student needs to have an GitHub account to participate in the GiPHouse courses, authentication is based on GitHub OAuth. This removes the need to save separate usernames and passwords. Instead of usernames and passwords, the website uses GitHub IDs to authenticate users.

A [custom user model](https://docs.djangoproject.com/en/dev/topics/auth/customizing/#using-a-custom-user-model-when-starting-a-project) (called `Employee`) has been created to make this possible.

### GitHub OAuth
The website has single click login because it uses [GitHub's OAuth implementation](https://developer.github.com/apps/building-oauth-apps/authorizing-oauth-apps/).

The GiPHouse GitHub organization has a GitHub App set up which is used for both repository synchronisation (explained later) and GitHub OAuth, which allows users to authorize the GiPHouse GitHub organization to see (limited) information about them. This App has credentials (a client ID and a client secret key), which are loaded into the Django settings using environment variables.

The authentication flow is as follows.
1. A user requests to login or register.
2. The user is redirected to `https://github.com/login/oauth/authorize`.
3. If the user has not authorized the GiPHouse GitHuB (OAuth) App, GitHub asks the user to do so.
4. If the user has authorized the GiPHouse Github (OAuth) App, they are redirected to the GiPHouse website with a temporary code as GET parameter.
5. The website uses this code to request an access token from the GitHub API.
6. The website uses the access token to request information about the user.

To support this authentication flow, [a custom authentication backend](https://docs.djangoproject.com/en/dev/topics/auth/customizing/) (called `GithubOAuthBackend`) has been created.

#### Creating Admin Users
Admin users (i.e. teacher, director or student assistant) do not have to register, they need to be created manually. In the backend it is possible to add new users. Every user should have their GitHub ID and GitHub username set. To promote a user to superuser, they should have the "Staff status", "Active" and "Superuser status" checkboxes checked.

### Semesters
The website makes the distinction between the spring semester (February - August) and the fall semester (September - January). Most of the content on the site is split by semester and year, because the content of the course that are given in the spring semester generally have nothing to do with the courses of the fall semester.

### Registrations
Every semester has a registration start and end date. Users will be able to between the start and end of the registration. They can do this by going to [https://giphouse.nl/register/](https://giphouse.nl/register/).

The registration process consists of two steps:
1. Authorizing the GiPHouse GitHub (OAuth) App.
2. A form that asks question about the registration (e.g. email, student number and project preferences).

The project preference is required to fill in during the registration, but registrations can be deleted later if necessary if for instance a project which people gave as preference is being discontinued. 

If multiple semesters have open registrations at one moment, the chronologically newest semester is picked. For example, if the fall 2019 and spring 2020 semester both allow registrations at one moment, users will register for the spring 2020 semester (even if at the moment of registration it is officially fall 2019).

It is possible for users to register multiple times. For example, if a user wants to follow a course in the fall semester and a different course in the spring semester. However, users cannot register multiple times within the same semester.

There is no built-in support for directors (which will look like registrations that are not appointed to a project).

#### Automatic team creation
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

### Questionnaires
During the courses, the students need to fill out surveys about the course, their project progress and their team. Admin users are able to create questionnaires and view submission by students in the backend. 

The questions in the questionnaires are of the following types:
1. Poor/good likert scale,
2. Disagree/agree likert scale and
3. Open question.

It is also possible to ask a question multiple times about each teammate. 

Questionnaires have a soft deadline and a hard deadline, which allows students to submit their answers late (i.e. after the soft deadline but before the hard deadline).

### Room Reservations
The room reservation is built using [FullCalendar](https://fullcalendar.io/), a popular JavaScript Calendar. FullCalendar allows users to drag rooms that they want to reserve into timeslots. FullCalendar makes requests to the website to save changes in the database. The rooms are created in the backend by admin users.

### Course, Project and Static Information
Admin users can add information about the course lectures and the projects in the backend. There are also a small amount of static HTML webpages with information about GiPHouse.

### Projects, Repositories and AWS
#### GitHub Synchronization
The projects module provides synchronisation functionality with a GitHub organization using the [GitHub API v3](https://developer.github.com/v3/). For this, a repository model is included in Django. Project(team)s can have one or multiple repositories, which are then synchronised with GitHub. For this functionality, a [GitHub App](https://developer.github.com/v3/apps/) must be registered and installed in the organization. Details on this are explained later.

Projects and repositories contain a field `github_team_id` and `github_repo_id` that corresponds to the respective `id` of the object on GitHub. These fields are automatically set and should not be touched under normal circumstances. Teams and repositories on GitHub that do not match one of these id's will not be touched by the GitHub synchronization. 
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

Synchronization can only be initialized via actions on specific sets of objects in their changelists, or via the big 'synchronize to GitHub' button (to perform synchronization on all objects) in the admin. Synchronization is implemented in a [idempotent](https://en.wikipedia.org/wiki/Idempotence) manner. 

Synchronization currently does not regard the role of directors of GipHouse. This needs to be configured manually. Note that it is however not possible to add directors manually to a team on GitHub, since they will be removed after each sync.

#### AWS Synchronization
The projects module provides synchronisation functionality with [AWS Organizations](https://aws.amazon.com/organizations/) using the official [boto3 Python AWS SDK](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html).
The AWS synchronisation process only applies to the current semester and is one-directional (from GiPHouse to AWS, but not vice versa).

Each project in the current semester with a team mailing list gets its own AWS member account that is part of GiPHouse's AWS organization.
Since all AWS member accounts have isolated environments, each team is able to configure their own AWS environment as desired.
The AWS member accounts are restricted in their abilities using a pre-configured [SCP policy](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps.html) that is applied to the course semester Organizational Unit (OU) where all team member accounts reside.
For example, the SCP policy can be set such that only (certain types of) [EC2](https://aws.amazon.com/ec2/) instances may be launched.
Such specific configuration details can be found under the [Getting Started](#registering-an-aws-environment-for-synchronisation) section.

The entire AWS synchronization process, also referred to as the pipeline, can be initiated in the Django admin interface under Projects by pressing the large `SYNCHRONIZE PROJECTS OF THE CURRENT SEMESTER TO AWS` at the top-right and roughly goes through the following stages:

1. Preliminary checks
    - Pipeline preconditions
        1. Locatable boto3 credentials and successful AWS API connection
        2. Check allowed AWS API actions based on IAM policy of caller
        3. Existing organization for AWS API caller
        4. AWS API caller acts under same account ID as organization's management account ID
        5. SCP policy type feature enabled for organization
    - Edge case checks
        1. No duplicate course semester OU names
2. Create current course semester OU (if non-existent)
3. Attach SCP policy to current course semester OU (if non-existent)
4. Synchronization
    - Determine new accounts to be invited based on AWS and GiPHouse data.
5. Create new AWS member accounts in AWS organization
6. Move new AWS member accounts to course semester OU

![pipeline-flowchart](resources/pipeline-flowchart.drawio.png)

After the synchronization process has finished, a response box is returned indicating success (green), soft-fail (orange) or hard-fail (red).
Verbose details for each synchronization run is logged using the `logging` module and can be accessed in the backend. for example to inspect causes of failed runs.

An example of a possible AWS Organizations environment in the form a tree is the following:
```
base (root/OU)
│
├── Fall 2022 (OU)
│   ├── team-alice@giphouse.nl (member account)
│   └── team-bob@giphouse.nl (member account)
│
├── Spring 2023 (OU)
│   ├── team-charlie@giphouse.nl (member account)
│   └── team-david@giphouse.nl (member account)
│
└── admin@giphouse.nl (management account)
```

The "base" (either root or OU), under which all relevant resources are created and operated on as part of the synchronization process, offers flexibility by being configurable in the Django admin panel.

When an AWS member account has been created for a team mailing list as part of an AWS Organization, an e-mail is sent by AWS.
This process might take some time and is under AWS' control.
It is important to be aware that gaining initial access to the member account is only possible by formally resetting the password; there is no other way.
Also note well that each project team member will receive such mails because the team mailing list works as a one-to-many mail forwarder.

By default, all newly created member accounts under an AWS organization are placed under root.
Once the member accounts have been created under root, they are automatically moved to the current course semester OU.
Note that: (1) it is not possible to create a new member account that gets placed in a specific OU and (2) new requested member accounts can not be moved unless the account creation has been finalized to `SUCCESS` and AWS does not specify an upper bound for the time it takes for a new member account creation to finalize.

Due to point (2), the code contains the variables `ACCOUNT_REQUEST_MAX_ATTEMPTS` for the number of times to check the status of a new member account request, and `ACCOUNT_REQUEST_INTERVAL_SECONDS` for the time to wait in between attempts.
These values are currently hard-coded and can be tweaked, should they cause problems with the synchronization process.

Points (1) and (2) pose the possibility of there being a time period between having a newly created member account under root and moving it to its corresponding OU that is restricted with an attached SCP policy, possibly giving the member account excessive permissions.
To mitigate this risk, every newly created account comes with a pre-defined [tag](https://docs.aws.amazon.com/tag-editor/latest/userguide/tagging.html) and the SCP policy attached to root should deny all permissions for accounts under root with the specific tag (see [Getting Started](#registering-an-aws-environment-for-synchronisation) section for more details on SCP policy and tag configuration).
The tag then automatically gets removed after the account has been moved to its destination course semester OU.

### Mailing Lists
Admin users can create mailing lists using the Django admin interface. A mailing list can be connected to projects, users and 'extra' email addresses that are not tied to a user. Relating a mailing list to a project implicitly makes the members of that project a member of the mailing list. Removing a mailing list in the Django admin will result in the corresponding mailing list to be archived or deleted in G suite during the next synchronization, respecting the 'archive instead of delete' property of the deleted mailing list. To sync a mailing list with G Suite, one can run the management command: `./manage.py sync_mailing_list` or use the button in the model admin. This will sync all mailing lists and the automatic lists into G Suite at the specified domain.

This sync starts by creating groups in G Suite for all mailing lists currently not in there, after they are created a request is done per member of that group to add them to the group. For the already existing groups a list is made of existing members in the group and the needed inserts or deletes are done to update the group.

### Tasks
A task is a process that takes more time than can fit in a request. The process is run in a separate thread and the status is synced to the task. The task is then used to show the user the progress and redirect them when it is finished.

### Styling
[Bootstrap](https://getbootstrap.com/) and [Font Awesome](https://fontawesome.com/) are used to style the website. Their respective SCSS versions are used.

## Development and Contributing
The website (and Django) have features to make developing and testing changes to the code locally easy.

The website has multiple settings. By default, the development settings are used.

### Getting Started
Follow the following steps to setup your own personal development environment.
1. Install Python 3.8+ and [poetry](https://poetry.eustace.io/).
2. Clone this repository.
3. Run `poetry install` to install all dependencies into virtual environment.
4. Run `poetry shell` to enter the virtual environment.
5. Run `python website/manage.py migrate` to initialize the database.
6. Run `python website/manage.py runserver` to start the local testing server.
7. Run `python website/manage.py runserver` again, to make sure the server discovers the just created `/static/` files.

#### Logging into the Backend
Because the authentication is based on Github OAuth authentication, some setup is required for users to be able to login in their own development environment.
You will need to set up [your own GitHub App](https://developer.github.com/apps/building-github-apps/creating-a-github-app/) that we will use for OAuth (and for repository synchronisation as well, as explained in the next step) and set your client ID and client secret key as environment variables (`DJANGO_GITHUB_CLIENT_ID` and `DJANGO_GITHUB_CLIENT_SECRET` respectively). [direnv](https://direnv.net/) is a tool that allows Linux users to do this automatically.

You will then be able to create a new superuser with the `createsuperuser` management command.
```Bash
$ python website/manage.py createsuperuser --github_id=<your_github_id> --github_username=<your_github_username> --no-input
```

#### Registering a GitHub App for repository synchronisation
To enable the synchronisation functionality of repositories and project(team)s, a GitHub App must be registered and installed in an organization. This GitHub App needs the following permissions:

- Repository/Metadata: read-only
- Repository/Administration: read and write
- Organization/Members: read and write
- User/Email addresses: read-only

We assume you already have a [GitHub organization](https://help.github.com/en/github/setting-up-and-managing-organizations-and-teams/creating-a-new-organization-from-scratch) setup.

- As an organization, you can develop a GitHub app and register this app at GitHub. People can then install that app in their own account or organization, giving your app access to that account or organization.
For this project, you will need to first [create your own GitHub app](https://developer.github.com/apps/building-github-apps/creating-a-github-app/) and then install it in your organization. 
After this, you can find a `DJANGO_GITHUB_SYNC_APP_ID`, and download the RSA `DJANGO_GITHUB_SYNC_APP_PRIVATE_KEY`. To use this key, encode it `base64` to `DJANGO_GITHUB_SYNC_APP_PRIVATE_KEY_BASE64`. These will be used as environment variables in this project and need to be set as GitHub Actions secrets in the repository (which will be explained later). 

- After the app is created, it needs to be [installed in your own organization](https://developer.github.com/apps/installing-github-apps/) (although technically speaking, it is also possible to publish the app in the previous step and install the app in a different organization!).
On installation, you can find the `DJANGO_GITHUB_SYNC_APP_INSTALLATION_ID` which we also need to set in this project. This installation id is hidden in the overview of installed GitHub Apps in your organization.
Additionally, you need to set the `DJANGO_GITHUB_SYNC_ORGANIZATION_NAME` to the name of the organization the app is installed in.

#### Registering a G Suite service account for mailing list synchronisation
To enable the synchronisation feature of mailing lists to G Suite, a project and service account need to be setup.

- Create a project in the [google cloud console](https://console.cloud.google.com).
- Create a [service account and credentials](https://developers.google.com/admin-sdk/directory/v1/guides/delegation#create_the_service_account_and_credentials).
- Enable [domain wide delegation of authority](https://developers.google.com/admin-sdk/directory/v1/guides/delegation#delegate_domain-wide_authority_to_your_service_account), with the scopes:
  - `https://www.googleapis.com/auth/admin.directory.group` (for accessing groups and adding or deleting members)
  - `https://www.googleapis.com/auth/apps.groups.settings` (for changing settings of groups and adding aliases)
- If this is the first time using the Groups Settings API, [enable it for the project](https://developers.google.com/apps-script/guides/services/advanced#enabling_advanced_services).

The credentials and admin user can then be setup in Github secrets. The email of the G Suite user used to manage to the G Suite domain has to be stored in the Github secret `DJANGO_GSUITE_ADMIN_USER`. The credentials json file has to be `base64` encoded and stored in the Github secret `DJANGO_GSUITE_ADMIN_CREDENTIALS_BASE64` (you can use the linux command `base64` for encoding the json file).

#### Registering an AWS environment for synchronisation
To enable the AWS synchronisation feature, the following points need to be configured only once in advance:

- Create AWS Organizations with all features enabled.
  - Ensure Service Control Policies (SCPs) feature is enabled.
  - Enable AWS CloudTrail for logging account activity (optional, recommended).
- Increase AWS Organizations quota for maximum number of member accounts to expected amount.
  - Default quota is set to 10.
  - Expected amount should be at least the number of unique projects in the current semester.
- Set AWS API credentials for `boto3` as environment variables.
  - `AWS_ACCESS_KEY_ID`: access key for AWS account.
  - `AWS_SECRET_ACCESS_KEY`: secret key for AWS account.
  - **(!)** Currently not automated using GitHub secrets.
- AWS API caller has sufficient permissions for all synchronization actions.
  - AWS API caller is IAM user acting on behalf of the management account of the AWS Organizations.
    - Ensure you are logged in as the management account when creating the IAM user for API access.
  - Pre-defined IAM policies `AWSOrganizationsFullAccess` and `IAMFullAccess` are more than sufficient.
  - **(!)** Restrictive custom IAM policy adhering to the principle of least privilege is recommended.
- Create SCP policies under AWS Organizations.
  - SCP policy restricting member accounts under root with a custom key-value tag.
    - Manually attach policy to root.
  - SCP policy for course semester OUs (e.g. to only allow EC2 resources of a specific type).
    - Automatically attached to course semester OUs.
- Configure a current AWS Policy under `Projects/AWS Policies` in the Django admin panel.
  - Set the base ID (root or OU) value.
  - Set the SCP policy ID value for course semester OUs.
  - Set the restricting custom key-value tag specified in the root SCP policy.
  - Mark the `Is current policy` checkbox to make the configuration active.

### Dependency Management
The Python dependencies are managed using a tool called [Poetry](https://python-poetry.org/), which automatically creates virtual environments that ease development and makes it easy to manage the dependencies. See the [Poetry documentation](https://python-poetry.org/docs/) for more information.

### Fixtures
To make testing in your development environment easier, the management command `createfixtures` exists. This management command creates dummy data in your local database.
```Bash
$ python website/manage.py createfixtures
```

Use the `--help` argument to get more information.

### Tests
To make sure everything functions correctly, the website has tests (using [Djangos built-in test framework](https://docs.djangoproject.com/en/dev/topics/testing/)). To run these manually use
```Bash
$ python website/manage.py test website/
```

### Code quality
The code of this project has high standards. This is enforced by continuous integration ([GitHub Actions](https://help.github.com/en/actions/automating-your-workflow-with-github-actions)).

- [PEP 8](https://www.python.org/dev/peps/pep-0008/) (Python styling) is enforced by using [Black](https://github.com/psf/black) and [flake8](https://gitlab.com/pycqa/flake8).
  - `black` is a tool that formats Python code. It is meant to be run on Python code and always return the same well-formatted code. This removes the need of manually formatting Python code, because if a formatting mistake is made, running `black` on the project will fix the mistake.
- Test coverage (both statement and branch coverage) is enforced by using [Coverage.py](https://coverage.readthedocs.io/en/coverage-5.0.3/).
  - The website has 100% test coverage.
- [PEP 257](https://www.python.org/dev/peps/pep-0257/) (Python docstring conventions) is enforced by [`pydocstyle`](https://github.com/PyCQA/pydocstyle).
  - PEP 257 forces every function, method and class to have documentation.

## Deployment
Django is only a web framework it cannot run without a web server and a database. Django needs a WSGI server to run the Python code. We use `uWSGI`. `uWSGI` needs a webserver that handles the web traffic, for this we use `NGINX` (which also handles all the static files). In development a simple SQLite3 database is used, because it is easy to setup and easy to delete. In production a more robust solution is necessary, that is why Postgres is used as production database.

### Docker
The website is meant to be run as a Docker container on a Linux server. The use of Docker containers, allows us to create a tailor-made environment (a Docker image) that has all the dependencies (i.e. files, libraries and packages) pre-installed. 

#### Dockerfile
The [Dockerfile](https://docs.docker.com/engine/reference/builder/) which steps should be executed to create the Docker image. This Docker image has all dependencies and the source code of the website. It also specifies that the production settings should be used.

#### Entrypoint
The entrypoint (`/usr/local/bin/entrypoint.sh` inside the Docker image) is executed whenever a container is created from the Docker image, it waits for the Postgres database to come up, makes the necessary changes to the static files and the database, creates a superuser (if it does not exist yet) and starts `uWSGI`.

#### GitHub Packages
A Docker image of the website ([docker.pkg.github.com/giphouse/website/production](https://github.com/GipHouse/Website/packages/356257)) is available on GitHub Packages. This image is refreshed every time a change is merged into the `master` branch.

#### Docker Compose
`docker-compose` is a tool that allows us to run multiple Docker containers that are connected to make them work together. Please see the [`docker-compose.yaml`](resources/docker-compose.yaml.template) file for the exact settings. This file contains all the configuration to pass the correct environment variables to the containers and save the correct files to the host.  

The following services are created by `docker-compose`.

##### `nginx`
[`nginx-proxy`](https://github.com/jwilder/nginx-proxy) is a Docker image containing that automatically generates correct `NGINX` configuration for other Docker Images. It listens on port 80 (HTTP) and 443 (HTTPS) and acts as the main access point for all web traffic to the website.

##### `letsencrypt`
[`letsencrypt-nginx-proxy-companion`](https://github.com/JrCs/docker-letsencrypt-nginx-proxy-companion) is a Docker image that uses Let's Encrypt to request a TLS certificate to make the website available over HTTPS.`

##### `postgres`
Runs a Postgres Database.

##### `web`
[`giphouse/giphousewebsite`](https://hub.docker.com/r/giphouse/giphousewebsite) is the Docker image that runs the actual website using `uWSGI` as server.

### Deployment Pipeline
#### `deploy.yaml` workflow
Whenever a change is merged into the `master` branch, the `deploy.yaml` GitHub Actions workflow is run. This workflow does the following:

##### `build-docker` job
1. Build a Docker image using the `master` branch.
2. Push the Docker image to GitHub Packages.

##### `deploy` job
After the `build-docker` job is finished, the `deploy` job runs.
1. Sets up SSH key that allows the runner to login to the production server using SSH.
2. Fills in passwords and secrets in the necessary files.
3. Create the necessary directories and files on the production server.
4. Pulls the new Docker image.
5. Restarts the production website with the new Docker image.
6. Purge all old unused Docker images.

#### Secrets
This repository is public and the GitHub Actions CI runner logs are also public, but some deployment information is secret. The secret information is setup using [GitHub repository secrets](https://help.github.com/en/actions/automating-your-workflow-with-github-actions/creating-and-using-encrypted-secrets). These are passed as environment variables to the GitHub Actions CI runners. The following secrets are setup.
- `DJANGO_SECRET_KEY`: The [`SECRET_KEY`](https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-SECRET_KEY) for Django.
- `DJANGO_GITHUB_SYNC_APP_ID`: The App ID of the registered GitHub App installed in the GiPHouse organization.
- `DJANGO_GITHUB_SYNC_APP_PRIVATE_KEY_BASE64`: The private RSA key ([PEM formatted](https://en.wikipedia.org/wiki/Privacy-Enhanced_Mail)) of the registered GitHub App installed in the GiPHouse organization, `base64` encoded.
- `DJANGO_GITHUB_SYNC_APP_INSTALLATION_ID`: The Installation ID of the registered GitHub App installed in the GiPHouse organization.
- `DJANGO_GITHUB_SYNC_ORGANIZATION_NAME`: The name of the organization the registered GitHub App is installed in.
- `DJANGO_GITHUB_CLIENT_ID`: The GiPHouse organization GitHub (OAuth) App client ID.
- `DJANGO_GITHUB_CLIENT_SECRET`: The GiPHouse organization GitHub (OAuth) App client secret key.
- `DJANGO_GITHUB_SYNC_SUPERUSER_ID`: The Github ID of the initial superuser.
- `DJANGO_GSUITE_ADMIN_USER`: The user which the G Suite api will impersonate when logging in with the credentials.
- `DJANGO_GSUITE_ADMIN_CREDENTIALS_BASE64`: The G Suite service account key file in json format, then `base64` encoded.
- `POSTGRES_NAME`: The name of the Postgres database.
- `POSTGRES_USER`: The username that is used to interact with the Postgres database.
- `POSTGRES_PASSWORD`: The password that is used to interact with the Postgres database.
- `SSH_USER`: The user that the CI runner uses to login to the production server using SSH. This user should be allowed to use Docker (e.g. be a member of the `docker` group).
- `SSH_PRIVATE_KEY`: The private key that allows the `SSH_USER` user to login to the production server using SSH.

### Server Configuration
The current server is an Amazon Web Services Elastic Cloud Computing (AWS EC2) instance that runs Ubuntu 18.04. EC2 instances have a default `ubuntu` user, that is allowed to execute `sudo` without password. The `docker-compose.yaml` file includes all services that are necessary to run the website in a production environment. That is why Docker is the only dependency on the host.

These steps are the necessary setup for a production server.

1. Add the SSH public keys of engineers to the `authorized_keys` of the `ubuntu` user.
2. Disable SSH password login.
3. Install `docker` and `docker-compose`.
4. Add the `ubuntu` user to the `docker` group.
5. Add the public key of the `SSH_PRIVATE_KEY` GitHub secret to the `authorized_keys` file of the `SSH_USER` GitHub secret user.
6. Change the url of the website by changing the `DEPLOYMENT_HOST` env variable in the deploy.yaml file. This will set the host in all necessary places.

### Keeping Everything Up to Date
All moving parts should be regularly updated to make sure all code is up to date and secure. There is no process in place to automate updates, because that may break something.
The following 

1. The Ubuntu server should be updated.
2. The Python dependencies should be updated (through `poetry`).
3. The JavaScript, font and [S]CSS files should be updated by replacing the current files with new ones.
