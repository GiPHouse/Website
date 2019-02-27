# from unittest import mock

from django.test import TestCase, Client
from django.contrib.auth.models import User
from peer_review.models import Question


class PeerReviewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.test_user = User.objects.create_user(
            username='myself',
        )
        User.objects.create_user(
            username='Jack',
        )

        Question.objects.create(
            question='Open Question global',
            question_type='o',
            about_someone_else=False
        )
        Question.objects.create(
            question='Closed Question global',
            question_type='a',
            about_someone_else=False
        )
        Question.objects.create(
            question='Open Question to peer',
            question_type='o',
            about_someone_else=True
        )
        Question.objects.create(
            question='Closed Question to peer',
            question_type='a',
            about_someone_else=True
        )
        cls.questions = Question.objects.all()

    def setUp(self):
        self.client = Client()

    def test_get_form(self):
        """
        Test GET request to form view
        """
        response = self.client.get('/peer_review/')
        print("BOOOP!")
        self.assertEqual(response.status_code, 200)

    def test_post_form(self):
        """
        Test POST request to form view
        """
        pass