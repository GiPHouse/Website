from django.contrib.auth import get_user_model
from django.contrib.auth.models import User as DjangoUser
from django.test import TestCase
from django.utils import timezone

from peer_review.models import Answer, Question, QuestionTypes, Questionnaire

User: DjangoUser = get_user_model()


class PeerReviewTest(TestCase):

    @classmethod
    def setUpTestData(cls):

        user = User.objects.create(
            username='user'
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

    def test_open_questionnaires(self):
        self.assertEqual(
            self.questionnaire,
            Questionnaire.objects.open_questionnaires().first()
        )

    def test_str_questionnaire(self):
        self.assertEqual(str(self.questionnaire), self.questionnaire.title)
