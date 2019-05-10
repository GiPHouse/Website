import random
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import User as DjangoUser
from django.core.management import BaseCommand
from django.utils import timezone

from faker import Faker
from faker.providers import address, company, date_time, internet, lorem, person

from courses.models import Course, Lecture, Semester

from questionnaires.models import AgreementAnswerData, Answer, OpenAnswerData, QualityAnswerData, Question, \
    Questionnaire, QuestionnaireSubmission

from projects.models import Client, Project

from registrations.models import GiphouseProfile, Registration, RoleChoice

from room_reservation.models import Reservation, Room

User: DjangoUser = get_user_model()

fake = Faker()
fake.add_provider(date_time)
fake.add_provider(company)
fake.add_provider(person)
fake.add_provider(address)
fake.add_provider(lorem)
fake.add_provider(internet)


class Command(BaseCommand):
    """Add the createfixtures command to manage.py."""

    help = 'Creates basic model instances for local testing'
    things = ['lecture', 'project', 'student', 'director', 'questionnaire', 'question', 'submission', 'room',
              'reservation']

    def add_arguments(self, parser):
        """Add all the arguments used by the createfixtures command."""
        for thing in self.things:
            parser.add_argument(
                f'--{thing}',
                type=int,
                help=f"The amount of fake {thing}s to add"
            )

    def create_base(self):
        """Create basic instances used by other fixtures."""
        Semester.objects.get_or_create(
            year=timezone.now().year,
            season=Semester.FALL,
            defaults={
                'registration_start': timezone.now() - timedelta(days=90),
                'registration_end': timezone.now() - timedelta(days=60),
            }
        )
        Semester.objects.get_or_create(
            year=timezone.now().year,
            season=Semester.SPRING,
            defaults={
                'registration_start': timezone.now() - timedelta(days=30),
                'registration_end': timezone.now() + timedelta(days=30),
            }
        )

    def create_lecture(self):
        """Create one fake lecture."""
        Lecture.objects.create(
            date=fake.date_between(start_date="-2m", end_date="+1w"),
            course=Course.objects.order_by('?').first(),
            semester=Semester.objects.order_by('?').first(),
            title=fake.catch_phrase(),
            description=' '.join(fake.sentences(nb=4)),
            teacher=fake.name(),
            location=f'{fake.street_name()} {fake.building_number()}',
        )

    def create_project(self):
        """Create one fake project."""
        client = Client.objects.create(
            name=fake.company()
        )
        Project.objects.create(
            name=(fake.word().capitalize() + ' '
                  + random.choice(['Creator', 'Builder', 'To ' + fake.file_extension(), 'Reader', 'Website', 'App',
                                   'Solution', 'In The Cloud', 'As A Service', 'Using Blockchain'])),
            semester=Semester.objects.order_by('?').first(),
            description=' '.join(fake.paragraphs(nb=3)),
            client=client,
        )

    def create_student(self):
        """Create one fake student."""
        github_id = random.randint(1, 999999)
        user = User.objects.create(
            username='github_' + str(github_id),
            email=fake.ascii_free_email(),
            first_name=fake.first_name(),
            last_name=fake.last_name(),
        )
        user.groups.add(Project.objects.order_by('?').first())
        user.save()
        GiphouseProfile.objects.create(
            user=user,
            github_id=github_id,
            github_username=fake.user_name(),
            student_number=fake.bothify("s#######"),
            role=random.choice([RoleChoice.se.name, RoleChoice.sdm.name])
        )
        Registration.objects.create(
            user=user,
            preference1=Project.objects.order_by('?').first(),
            comments=random.choice([fake.sentence(), ''])
        )

    def create_director(self):
        """Create one fake director."""
        github_id = random.randint(1, 999999)
        user = User.objects.create(
            username='github_' + str(github_id),
            email=fake.ascii_free_email(),
            first_name=fake.first_name(),
            last_name=fake.last_name(),
        )
        user.groups.add(Project.objects.order_by('?').first())
        user.save()
        GiphouseProfile.objects.create(
            user=user,
            github_id=github_id,
            github_username=fake.user_name(),
            student_number=fake.bothify("s#######"),
            role=RoleChoice.director.name,
        )

    def create_questionnaire(self):
        """Create one fake questionnaire."""
        Questionnaire.objects.create(
            title=fake.sentence(),
            semester=Semester.objects.order_by('?').first(),
            available_from=timezone.now() - timedelta(days=2),
            available_until_soft=timezone.now() + timedelta(days=10),
            available_until_hard=timezone.now() + timedelta(days=15),
        )

    def create_question(self):
        """Create one fake question."""
        Question.objects.create(
            questionnaire=Questionnaire.objects.order_by('?').first(),
            question=fake.sentence().replace('.', '?'),
            question_type=random.choice(Question.CHOICES)[0],
            about_team_member=random.choice([True, False])
        )

    def create_submission(self):
        """Create one fake submission."""
        questionnaire = Questionnaire.objects.order_by('?').first()
        user = User.objects.exclude(questionnairesubmission__questionnaire=questionnaire).order_by('?').first()
        peers = User.objects.exclude(pk=user.pk).filter(
            groups__in=user.groups.filter(project__semester=Semester.objects.first())
        )

        submission = QuestionnaireSubmission.objects.create(
            questionnaire=questionnaire,
            participant=user,
            late=random.choice([True, False]),
            created=fake.date_between(start_date='-2d', end_date='today'),
        )

        def create_answer(question, answer):
            """Create a fake answer for the question."""
            if question.question_type == Question.OPEN:
                OpenAnswerData.objects.create(
                    answer=answer,
                    value=fake.paragraph()
                )
            elif question.question_type == Question.AGREEMENT:
                AgreementAnswerData.objects.create(
                    answer=answer,
                    value=random.choice(AgreementAnswerData.CHOICES)[0]
                )
            elif question.question_type == Question.QUALITY:
                QualityAnswerData.objects.create(
                    answer=answer,
                    value=random.choice(QualityAnswerData.CHOICES)[0]
                )

        for question in questionnaire.question_set.all():
            if question.about_team_member:
                for peer in peers:
                    answer = Answer.objects.create(
                        question=question,
                        submission=submission,
                        peer=peer
                    )
                    create_answer(question, answer)
            else:
                answer = Answer.objects.create(
                    question=question,
                    submission=submission
                )
                create_answer(question, answer)

    def create_room(self):
        """Create one fake room."""
        Room.objects.create(
            name=fake.city(),
            location=fake.numerify('Mercator 1.0##')
        )

    def create_reservation(self):
        """Create one fake reservation."""
        time = fake.date_time_this_month(after_now=True, tzinfo=timezone.get_current_timezone())
        time = time.replace(minute=0, second=0, microsecond=0)
        Reservation.objects.create(
            reservee=User.objects.order_by('?').first(),
            room=Room.objects.order_by('?').first(),
            start_time=time,
            end_time=time + timedelta(hours=random.randint(1, 5))
        )

    def handle(self, *args, **kwargs):
        """Execute the createfixtures command."""
        options = {
            'lecture': 8,
            'project': 5,
            'student': 25,
            'director': 2,
            'questionnaire': 2,
            'question': 8,
            'submission': 23,
            'room': 2,
            'reservation': 10,
        }
        if any([value is not None for key, value in kwargs.items() if value in self.things]):
            options = dict()
        for key, value in kwargs.items():
            if value is not None:
                options[key] = value

        self.create_base()

        for thing in self.things:
            amount = options.get(thing) or 0
            self.stdout.write(f"Creating {amount} {thing}s")
            for _ in range(amount):
                self.__getattribute__('create_' + thing)()
