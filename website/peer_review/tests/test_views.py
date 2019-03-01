from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from peer_review.models import Question, Answer


def generate_post_data(questions, peers):
    post = {}
    for question in questions:
        if question.about_team_member:
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


class PeerReviewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='myself',
            password='123'
        )
        cls.peer = User.objects.create_user(
            username='Jack',
        )
        Question.objects.create(
            question='Open Question global',
            question_type='openQuestion',
            about_team_member=False
        )
        Question.objects.create(
            question='Closed Question global',
            question_type='agreeDisagree',
            about_team_member=False
        )
        Question.objects.create(
            question='Open Question to peer',
            question_type='openQuestion',
            about_team_member=True
        )
        Question.objects.create(
            question='Closed Question to peer',
            question_type='agreeDisagree',
            about_team_member=True
        )
        Question.objects.create(
            question='Closed Question to peer',
            question_type='poorGood',
            about_team_member=True
        )
        cls.questions = Question.objects.all()

    def setUp(self):
        self.client = Client()
        self.client.login(username='myself', password='123')

    def test_str_question(self):
        question = self.questions[0]
        str_question = str(question.question)
        self.assertEqual(str(question), str_question)

    def test_str_answer(self):
        a = "Something"
        answer = Answer.objects.create(
            participant=self.user,
            peer=self.peer,
            question=self.questions[0],
            answer=a,
        )
        str_answer = '({} about {}) {}:  answer {}'.format(
            self.user, self.peer, self.questions[0], a)
        self.assertEqual(str(answer), str_answer)

    def test_get_form(self):
        """
        Test GET request to form view
        """
        response = self.client.get(reverse('peer_review:form'))
        self.assertEqual(response.status_code, 200)

    def test_post_form(self):
        """
        Test POST request to form view
        """
        peers = User.objects.exclude(pk=self.user.pk)
        post = generate_post_data(self.questions, peers)
        response = self.client.post(
            reverse("peer_review:form"),
            post,
            follow=True
        )

        self.assertEqual(response.status_code, 200)

        for question in self.questions:
            if question.about_team_member:
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
