# from unittest import mock

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from peer_review.models import Question, Answer


class PeerReviewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='myself',
            password='123'
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
        Question.objects.create(
            question='Closed Question to peer',
            question_type='p',
            about_someone_else=True
        )
        cls.questions = Question.objects.all()

    def setUp(self):
        self.client = Client()
        self.client.login(username='myself', password='123')

    def test_get_form(self):
        """
        Test GET request to form view
        """
        response = self.client.get('/peer_review/')
        self.assertEqual(response.status_code, 200)

    def test_post_form(self):
        """
        Test POST request to form view
        """
        peers = User.objects.exclude(pk=self.user.pk)
        post = self.generate_post_data(peers)

        print(post)
        response = self.client.post(
            reverse("peer_review:show"),
            post,
            follow=True
        )

        self.assertEqual(response.status_code, 200)

        for question in self.questions:
            if question.about_someone_else:
                for peer in peers:
                    field_name = f"{peer}_{question.pk}"
                    answer_exists = Answer.objects.filter(
                        question=question,
                        participant=self.user,
                        peer=peer,
                        answer=post[field_name],
                    ).exists()
                    self.assertTrue(answer_exists)
            else:
                field_name = f"{question.pk}"
                answer_exists = Answer.objects.filter(
                    question=question,
                    participant=self.user,
                    answer=post[field_name],
                ).exists()
                self.assertTrue(answer_exists)

    def generate_post_data(self, peers):
        post = {}
        for question in self.questions:
            if question.about_someone_else:
                for peer in peers:
                    field_name = f"{peer}_{question.pk}"
                    if question.closed_question():
                        post[field_name] = question.get_scale_labels()[0]
                    else:
                        post[field_name] = "Something"
            else:
                field_name = f"{question.pk}"
                if question.closed_question():
                    post[field_name] = question.get_scale_labels()[0]
                else:
                    post[field_name] = "Something"
        return post
