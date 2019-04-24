from courses.models import SeasonChoice, Semester

from django.contrib.auth import get_user_model
from django.contrib.auth.models import User as DjangoUser
from django.test import TestCase
from django.utils import timezone

from projects.models import Project

from registrations.models import GiphouseProfile

User: DjangoUser = get_user_model()


class ModelsTest(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.first_name = 'Test'
        cls.last_name = 'Test'
        cls.project_name = 'testproject'

        cls.test_user = User.objects.create_user(
            username='test',
            first_name=cls.first_name,
            last_name=cls.last_name,
        )

        cls.test_giphouse_user = GiphouseProfile.objects.create(
            user=cls.test_user,
            github_id=1,
        )

        cls.test_semester = Semester.objects.create(
            year=timezone.now().year,
            season=SeasonChoice.spring.name,
            registration_start=timezone.now(),
            registration_end=timezone.now() + timezone.timedelta(days=1),
        )

        cls.test_project = Project.objects.create(
            name=cls.project_name,
            semester=cls.test_semester,
        )

    def test_season_str(self):
        self.assertEqual(SeasonChoice.spring.value, str(SeasonChoice.spring))

    def test_semester_str(self):

        self.assertEqual(
            f'{self.test_semester.get_season_display()} {self.test_semester.year}',
            str(self.test_semester)
        )

    def test_giphouseprofile_str(self):

        self.assertEqual(
            f'{self.first_name} {self.last_name}',
            str(self.test_giphouse_user)
        )

    def test_project_str(self):

        self.assertEqual(
            f'{self.project_name} ({self.test_semester})',
            str(self.test_project)
        )
