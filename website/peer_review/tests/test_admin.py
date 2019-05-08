from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User as DjangoUser
from django.shortcuts import reverse
from django.utils import timezone

from registrations.models import GiphouseProfile
from peer_review.models import Question, Answer, Questionnaire, QuestionTypes

User: DjangoUser = get_user_model()


class RegistrationAdminTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.admin_password = 'hunter2'
        cls.admin = User.objects.create_superuser(
            username='admin',
            email='',
            password=cls.admin_password)

        user = User.objects.create(username='user')
        GiphouseProfile.objects.create(
            user=user,
            github_id='0',
            github_username='user',
        )

        cls.questionnaire = Questionnaire.objects.create(
            title="An Active Questionnaire",
            available_from=timezone.now() - timezone.timedelta(days=2),
            available_until=timezone.now() + timezone.timedelta(days=1)
        )
        question = Question.objects.create(
            questionnaire=cls.questionnaire,
            question='Open Question global',
            question_type=QuestionTypes.open_question.name,
            about_team_member=False
        )

        cls.answer = Answer.objects.create(
            question=question,
            answer='answer text',
            participant=user,
        )

    def setUp(self):
        self.client = Client()
        self.client.login(username=self.admin.username, password=self.admin_password)

    def test_get_answer_changelist(self):
        response = self.client.get(
            reverse('admin:peer_review_answer_changelist'),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
