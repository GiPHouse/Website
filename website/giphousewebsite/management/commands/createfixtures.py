import random
from datetime import timedelta

from courses.models import Course, Lecture, SeasonChoice, Semester

from django.contrib.auth import get_user_model
from django.contrib.auth.models import User as DjangoUser
from django.core.management import BaseCommand
from django.utils import timezone

from faker import Faker
from faker.providers import address, company, date_time, internet, lorem, person

from projects.models import Client, Project

from registrations.models import GiphouseProfile, Registration, RoleChoice

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
    things = ['lecture', 'project', 'student', 'director']

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
            season=SeasonChoice.fall.name,
            defaults={
                'registration_start': timezone.now() - timedelta(days=90),
                'registration_end': timezone.now() - timedelta(days=60),
            }
        )
        Semester.objects.get_or_create(
            year=timezone.now().year,
            season=SeasonChoice.spring.name,
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

    def handle(self, *args, **options):
        """Execute the createfixtures command."""
        options = {
            'lecture': 8,
            'project': 5,
            'student': 25,
            'director': 2,
        }.update(options)

        self.create_base()

        for thing in self.things:
            amount = options[thing] or 0
            self.stdout.write(f"Creating {amount} {thing}s")
            for _ in range(amount):
                self.__getattribute__('create_' + thing)()
