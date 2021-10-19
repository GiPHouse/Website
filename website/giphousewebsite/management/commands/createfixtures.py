import random
import string

from django.contrib.auth import get_user_model
from django.core.management import BaseCommand
from django.db import IntegrityError
from django.db.models import Count
from django.utils import timezone
from django.utils.text import slugify

from faker import Faker
from faker.providers import address, company, date_time, internet, lorem, person

from courses.models import Course, Lecture, Semester


from mailing_lists.models import ExtraEmailAddress, MailingList, MailingListAlias, MailingListCourseSemesterLink

from projects.models import Client, Project, Repository

from questionnaires.models import (
    AgreementAnswerData,
    Answer,
    OpenAnswerData,
    QualityAnswerData,
    Question,
    Questionnaire,
    QuestionnaireSubmission,
)

from registrations.models import Employee, Registration

from room_reservation.models import Reservation, Room

User: Employee = get_user_model()

fake = Faker()
fake.add_provider(date_time)
fake.add_provider(company)
fake.add_provider(person)
fake.add_provider(address)
fake.add_provider(lorem)
fake.add_provider(internet)

DEFAULTS = {
    "lecture": 8,
    "project": 5,
    "student": 25,
    "questionnaire": 2,
    "question": 8,
    "submission": 23,
    "room": 2,
    "reservation": 10,
    "mailing_list": 3,
}
THINGS = list(DEFAULTS.keys())


class Command(BaseCommand):
    """Add the createfixtures command to manage.py."""

    help = "Creates basic model instances for local testing"

    def add_arguments(self, parser):
        """Add all the arguments used by the createfixtures command."""
        for thing in THINGS:
            parser.add_argument(
                f"--{thing}", type=int, help=f"The amount of fake {thing}s to add, default = {DEFAULTS[thing]}"
            )
        parser.add_argument(
            "--merge",
            action="store_true",
            help="Use default options, but overwrite with supplied command line options. "
            "The default behaviour is to ignore the default options when a "
            "command line option is supplied.",
        )

    def create_base(self):
        """Create basic instances used by other fixtures."""
        Semester.objects.get_or_create(
            year=timezone.now().year - 1,
            season=Semester.FALL,
            defaults={
                "registration_start": timezone.now() - timezone.timedelta(days=90),
                "registration_end": timezone.now() - timezone.timedelta(days=60),
            },
        )

        Semester.objects.get_or_create(
            year=timezone.now().year,
            season=Semester.SPRING,
            defaults={
                "registration_start": timezone.now() - timezone.timedelta(days=30),
                "registration_end": timezone.now() + timezone.timedelta(days=30),
            },
        )

        Semester.objects.get_or_create(
            year=timezone.now().year,
            season=Semester.FALL,
            defaults={
                "registration_start": timezone.now() + timezone.timedelta(days=60),
                "registration_end": timezone.now() + timezone.timedelta(days=90),
            },
        )

    def create_mailing_list(self):
        """Create one fake mailing list."""
        mailing_list = MailingList.objects.create(address=fake.slug(), description=fake.sentence())
        mailing_list.projects.set(random.sample(list(Project.objects.all()), random.randint(0, 2)))
        mailing_list.users.set(random.sample(list(User.objects.exclude(email="")), random.randint(0, 10)))

        course = Course.objects.first()
        semester = Semester.objects.first()
        MailingListCourseSemesterLink.objects.create(mailing_list=mailing_list, course=course, semester=semester)

        for i in range(random.randint(1, 2)):
            MailingListAlias.objects.create(address="alias-" + fake.slug(), mailing_list=mailing_list)
        for i in range(random.randint(0, 4)):
            ExtraEmailAddress.objects.create(
                address="extra-" + fake.safe_email(), name=fake.first_name(), mailing_list=mailing_list
            )

    def create_lecture(self):
        """Create one fake lecture."""
        Lecture.objects.create(
            date=fake.date_between(start_date="-2m", end_date="+1w"),
            course=Course.objects.order_by("?").first(),
            semester=Semester.objects.order_by("?").first(),
            title=fake.catch_phrase(),
            description=" ".join(fake.sentences(nb=4)),
            teacher=fake.name(),
            location=f"{fake.street_name()} {fake.building_number()}",
        )

    def create_project(self):
        """Create one fake project."""
        client = Client.objects.create(name=fake.company())
        ordered_semesters = Semester.objects.order_by("year", "season")
        first_semester = ordered_semesters.first()
        semester = (
            ordered_semesters.annotate(project_count=Count("project"))
            .exclude(project_count__gte=2, pk=first_semester.pk)
            .first()
        )
        repo_count = semester.project_set.count() % 3 + 1
        project = Project.objects.create(
            name=(
                fake.word().capitalize()
                + " "
                + random.choice(
                    [
                        "Creator",
                        "Builder",
                        "To " + fake.file_extension(),
                        "Reader",
                        "Website",
                        "App",
                        "Solution",
                        "In The Cloud",
                        "As A Service",
                        "Using Blockchain",
                    ]
                )
            ),
            semester=semester,
            description=" ".join(fake.paragraphs(nb=3)),
            client=client,
        )
        for i in range(repo_count):
            suffix = "" if i == 0 else f"-{i}"
            archived = i % 3
            Repository.objects.create(
                name=f"{slugify(project.name)}-{semester.get_season_display()}-{semester.year}{suffix}",
                project=project,
                private=True if i == 0 else random.choice([True, False]),
                is_archived=archived,
            )

    @staticmethod
    def generate_fake_github_username():
        """Generate a random username that isn't an existing Github username."""
        # Entropy should ensure we do not use real Github usernames (26 + 26 + 10)^39 = ~2^232
        return "".join(random.choices(string.ascii_letters + string.digits, k=39))

    @staticmethod
    def generate_partner_preference(semester):
        """Generate a partner preference string of a full name, full name with typo, random string or None value."""
        choices = ["".join(random.choices(string.ascii_letters + string.digits, k=10)), None]
        user = User.objects.filter(registration__semester=semester).order_by("?").first()
        if user:
            existing_user_name = user.get_full_name()
            choices.append(existing_user_name)

            # Swap two letters in an existing name
            i = random.randint(1, len(existing_user_name) - 1)
            c = list(existing_user_name.lower())
            c[i], c[i - 1] = c[i - 1], c[i]
            name_with_typo = "".join(c)

            choices.append(name_with_typo)

        return random.choice(choices)

    def create_student(self):
        """Create one fake student."""
        user = User.objects.create(
            email=fake.safe_email(),
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            github_id=random.randint(1, 999_999),
            github_username=self.generate_fake_github_username(),
            student_number=fake.bothify("s#######"),
        )
        project = Project.objects.order_by("?").first()

        Registration.objects.create(
            user=user,
            course=Course.objects.order_by("?").first(),
            semester=project.semester,
            project=project,
            preference1=Project.objects.order_by("?").first(),
            preference2=Project.objects.order_by("?").first(),
            preference3=Project.objects.order_by("?").first(),
            partner_preference1=self.generate_partner_preference(project.semester),
            partner_preference2=self.generate_partner_preference(project.semester),
            partner_preference3=self.generate_partner_preference(project.semester),
            is_international=random.choice([True, False]),
            comments=random.choice([fake.sentence(), ""]),
            experience=Registration.EXPERIENCE_INTERMEDIATE,
        )

    def create_questionnaire(self):
        """Create one fake questionnaire."""
        Questionnaire.objects.create(
            title=fake.sentence(),
            semester=Semester.objects.order_by("?").first(),
            available_from=timezone.now() - timezone.timedelta(days=2),
            available_until_soft=timezone.now() + timezone.timedelta(days=10),
            available_until_hard=timezone.now() + timezone.timedelta(days=15),
        )

    def create_question(self):
        """Create one fake question."""
        question_type = random.choice(Question.CHOICES)[0]
        Question.objects.create(
            questionnaire=Questionnaire.objects.order_by("?").first(),
            question=fake.sentence().replace(".", "?"),
            question_type=question_type,
            about_team_member=random.choice([True, False]),
            with_comments=False if question_type == Question.OPEN else random.choice([True, False]),
        )

    @staticmethod
    def _create_answer(question, answer):
        """Create a fake answer for the question."""
        if question.question_type == Question.OPEN:
            OpenAnswerData.objects.create(answer=answer, value=fake.paragraph())
        elif question.question_type == Question.AGREEMENT:
            AgreementAnswerData.objects.create(answer=answer, value=random.choice(AgreementAnswerData.CHOICES)[0])
        elif question.question_type == Question.QUALITY:
            QualityAnswerData.objects.create(answer=answer, value=random.choice(QualityAnswerData.CHOICES)[0])

        if question.with_comments and random.choice([True, False]):
            answer.comments = fake.sentence()

    def create_submission(self):
        """Create one fake submission."""
        questionnaire = Questionnaire.objects.order_by("?").first()
        user = (
            User.objects.exclude(questionnairesubmission__questionnaire=questionnaire)
            .exclude(registration__isnull=True)
            .order_by("?")
            .first()
        )
        user_project = Project.objects.get(registration__user=user)
        project_registrations = Registration.objects.filter(project=user_project)
        peers = User.objects.exclude(pk=user.pk).filter(registration__in=project_registrations)

        submission = QuestionnaireSubmission.objects.create(
            questionnaire=questionnaire,
            participant=user,
            late=random.choice([True, False]),
            created=fake.date_between(start_date="-2d", end_date="today"),
        )

        for question in questionnaire.question_set.all():
            if question.about_team_member:
                for peer in peers:
                    answer = Answer.objects.create(question=question, submission=submission, peer=peer)
                    self._create_answer(question, answer)
            else:
                answer = Answer.objects.create(question=question, submission=submission)
                self._create_answer(question, answer)

    def create_room(self):
        """Create one fake room."""
        Room.objects.create(name=fake.city(), location=fake.numerify("Mercator 1.0##"))

    def create_reservation(self):
        """Create one fake reservation."""
        time = fake.date_time_this_month(after_now=True, tzinfo=timezone.get_current_timezone())
        time = time.replace(minute=0, second=0, microsecond=0)
        Reservation.objects.create(
            reservee=User.objects.order_by("?").first(),
            room=Room.objects.order_by("?").first(),
            start_time=time,
            end_time=time + timezone.timedelta(hours=random.randint(1, 5)),
        )

    def handle(self, *args, **kwargs):
        """Execute the createfixtures command."""
        options = dict()

        if all([value is None for key, value in kwargs.items() if key in THINGS]) or kwargs["merge"]:
            self.stdout.write("Applying default options")
            options = DEFAULTS
        else:
            self.stdout.write("Only using user options")

        for key, value in kwargs.items():
            if value is not None:
                options[key] = value

        self.create_base()

        for thing in THINGS:
            amount = options.get(thing) or 0
            self.stdout.write(f"Creating {amount} {thing}s")
            for _ in range(amount):
                while True:
                    try:
                        self.__getattribute__("create_" + thing)()
                        break
                    except IntegrityError as e:
                        if "UNIQUE constraint failed" in str(e.__cause__):
                            self.stderr.write("IntegrityError, trying again")
                        else:
                            raise
