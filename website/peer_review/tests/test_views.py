from courses.models import Semester

from django.contrib.auth import get_user_model
from django.contrib.auth.models import User as DjangoUser
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from peer_review.forms import PeerReviewForm
from peer_review.models import Question, Questionnaire

from projects.models import Project

User: DjangoUser = get_user_model()


def generate_post_data(questionnaire_id, peers):
    post_data = {}
    for question in Question.objects.filter(questionnaire_id=questionnaire_id):
        if question.about_team_member:
            current_peers = peers
        else:
            current_peers = (None,)
        for peer in current_peers:
            field_name = PeerReviewForm.get_field_name(question, peer)
            if question.is_closed:
                post_data[field_name] = 0
            else:
                post_data[field_name] = "Something"
    return post_data


class PeerReviewTest(TestCase):

    @classmethod
    def setUpTestData(cls):

        semester = Semester.objects.create(
            year=2019,
            season=Semester.SPRING,
            registration_start=timezone.now(),
            registration_end=timezone.now() + timezone.timedelta(days=60)
        )

        cls.team = Project.objects.create(
            semester=semester,
            name="Test Project",
            description="Description",
        )
        cls.user = User.objects.create_user(
            username='myself',
            password='123',
        )
        cls.user.groups.add(cls.team)
        cls.user.save()

        cls.peer = User.objects.create_user(
            username='Jack',
        )
        cls.peer.groups.add(cls.team)
        cls.peer.save()

        cls.active_questions = Questionnaire.objects.create(
            semester=semester,
            title="An Active Questionnaire",
            available_from=timezone.now() - timezone.timedelta(days=2),
            available_until_soft=timezone.now() + timezone.timedelta(days=1),
            available_until_hard=timezone.now() + timezone.timedelta(days=1),
        )
        Question.objects.create(
            questionnaire=cls.active_questions,
            question='Open Question global',
            question_type=Question.OPEN,
            about_team_member=False
        )
        Question.objects.create(
            questionnaire=cls.active_questions,
            question='Closed Question global',
            question_type=Question.QUALITY,
            about_team_member=True
        )
        Question.objects.create(
            questionnaire=cls.active_questions,
            question='Closed Question global',
            question_type=Question.AGREEMENT,
            about_team_member=False
        )

        cls.late_questions = Questionnaire.objects.create(
            semester=semester,
            title="An Closed Questionnaire",
            available_from=timezone.now() - timezone.timedelta(days=3),
            available_until_soft=timezone.now() - timezone.timedelta(days=2),
            available_until_hard=timezone.now() + timezone.timedelta(days=1),
        )

        cls.closed_questions = Questionnaire.objects.create(
            semester=semester,
            title="An Closed Questionnaire",
            available_from=timezone.now() - timezone.timedelta(days=3),
            available_until_soft=timezone.now() - timezone.timedelta(days=2),
            available_until_hard=timezone.now() - timezone.timedelta(days=1),
        )

    def setUp(self):
        self.client = Client()
        self.client.login(username='myself', password='123')

    def test_get_overview(self):
        response = self.client.get(reverse('peer_review:overview'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Start Late')

    def test_get_questionnaire(self):
        response = self.client.get(
            reverse('peer_review:questionnaire', kwargs={'questionnaire': self.active_questions.id})
        )
        self.assertEqual(response.status_code, 200)

    def test_post_questionnaire(self):
        current_peers = User.objects.exclude(pk=self.user.pk)
        post_data = generate_post_data(self.active_questions.id, current_peers)

        response = self.client.post(
            reverse('peer_review:questionnaire', kwargs={'questionnaire': self.active_questions.id}),
            post_data,
            follow=True,
        )
        self.assertRedirects(response, reverse('home'))

    def test_post_questionnaire_twice(self):

        current_peers = User.objects.exclude(pk=self.user.pk)
        post_data = generate_post_data(self.active_questions.id, current_peers)

        response = self.client.post(
            reverse('peer_review:questionnaire', kwargs={'questionnaire': self.active_questions.id}),
            post_data,
            follow=True,
        )

        self.assertRedirects(response, reverse('home'))

        response = self.client.post(
            reverse('peer_review:questionnaire', kwargs={'questionnaire': self.active_questions.id}),
            post_data,
            follow=True,
        )

        self.assertContains(response, 'Questionnaire already submitted.')

    def test_post_closed(self):

        response = self.client.post(
            reverse('peer_review:questionnaire', kwargs={'questionnaire': self.closed_questions.id}),
            {},
            follow=True,
        )
        self.assertContains(response, 'Questionnaire is closed.')

    def test_all_questionnaires_visible(self):
        response = self.client.get(reverse('peer_review:overview'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.active_questions.title)
        self.assertContains(response, self.closed_questions.title)


class NoQuestionnairesTest(TestCase):
    def test_navbar_link_not_visible_with_no_questionnaires(self):
        response = self.client.get(reverse('home'))
        self.assertNotContains(
            response,
            'Peer Review',
        )
