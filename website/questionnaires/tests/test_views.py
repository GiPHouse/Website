from django.contrib.auth import get_user_model
from django.contrib.auth.models import User as DjangoUser
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from courses.models import Course, Semester, current_season

from projects.models import Project

from questionnaires.forms import QuestionnaireForm
from questionnaires.models import Question, Questionnaire

from registrations.models import Registration

User: DjangoUser = get_user_model()


def generate_post_data(questionnaire_id, peers):
    post_data = {}
    for question in Question.objects.filter(questionnaire_id=questionnaire_id):
        if question.about_team_member:
            current_peers = peers
        else:
            current_peers = (None,)
        for peer in current_peers:
            field_name = QuestionnaireForm.get_field_name(question, peer)
            if question.is_closed:
                post_data[field_name] = 1
            else:
                post_data[field_name] = "Something"
    return post_data


class QuestionnaireTest(TestCase):
    @classmethod
    def setUpTestData(cls):

        semester = Semester.objects.create(
            year=2019,
            season=current_season(),
            registration_start=timezone.now(),
            registration_end=timezone.now() + timezone.timedelta(days=60),
        )

        cls.team = Project.objects.create(semester=semester, name="Test Project", description="Description")
        cls.user = User.objects.create_user(username="myself", password="123")
        Registration.objects.create(
            user=cls.user,
            semester=semester,
            project=cls.team,
            course=Course.objects.sdm(),
            preference1=cls.team,
            experience=Registration.EXPERIENCE_ADVANCED,
        )

        cls.alone_user = User.objects.create_user(username="loner", password="123")

        cls.peer = User.objects.create_user(username="Jack")
        Registration.objects.create(
            user=cls.peer,
            semester=semester,
            project=cls.team,
            course=Course.objects.sdm(),
            preference1=cls.team,
            experience=Registration.EXPERIENCE_ADVANCED,
        )

        cls.active_questions = Questionnaire.objects.create(
            semester=semester,
            title="An Active Questionnaire",
            available_from=timezone.now() - timezone.timedelta(days=2),
            available_until_soft=timezone.now() + timezone.timedelta(days=1),
            available_until_hard=timezone.now() + timezone.timedelta(days=1),
        )

        cls.closed_questions = Questionnaire.objects.create(
            semester=semester,
            title="An Closed Questionnaire",
            available_from=timezone.now() - timezone.timedelta(days=3),
            available_until_soft=timezone.now() - timezone.timedelta(days=2),
            available_until_hard=timezone.now() - timezone.timedelta(days=1),
        )

        cls.late_questions = Questionnaire.objects.create(
            semester=semester,
            title="An Closed Questionnaire",
            available_from=timezone.now() - timezone.timedelta(days=3),
            available_until_soft=timezone.now() - timezone.timedelta(days=2),
            available_until_hard=timezone.now() + timezone.timedelta(days=1),
        )

        cls.closed_questionnaire = Questionnaire.objects.create(
            semester=semester,
            title="A Closed Questionnaire",
            available_from=timezone.now() - timezone.timedelta(days=3),
            available_until_soft=timezone.now() - timezone.timedelta(days=2),
            available_until_hard=timezone.now() - timezone.timedelta(days=1),
        )

        Question.objects.create(
            questionnaire=cls.active_questions,
            question="Open Question global",
            question_type=Question.OPEN,
            about_team_member=False,
        )
        Question.objects.create(
            questionnaire=cls.active_questions,
            question="Closed Question global",
            question_type=Question.QUALITY,
            about_team_member=True,
        )
        Question.objects.create(
            questionnaire=cls.active_questions,
            question="Closed Question global",
            question_type=Question.AGREEMENT,
            about_team_member=False,
        )

    def setUp(self):
        self.client = Client()
        self.client.login(username="myself", password="123")

    def test_get_overview(self):
        response = self.client.get(reverse("questionnaires:overview"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Start Late")

    def test_get_questionnaire(self):
        response = self.client.get(
            reverse("questionnaires:questionnaire", kwargs={"questionnaire": self.active_questions.id})
        )
        self.assertEqual(response.status_code, 200)

    def test_post_questionnaire(self):
        current_peers = User.objects.exclude(pk=self.user.pk)
        post_data = generate_post_data(self.active_questions.id, current_peers)

        response = self.client.post(
            reverse("questionnaires:questionnaire", kwargs={"questionnaire": self.active_questions.id}),
            post_data,
            follow=True,
        )
        self.assertRedirects(response, reverse("home"))

    def test_post_questionnaire_twice(self):

        current_peers = User.objects.exclude(pk=self.user.pk)
        post_data = generate_post_data(self.active_questions.id, current_peers)

        response = self.client.post(
            reverse("questionnaires:questionnaire", kwargs={"questionnaire": self.active_questions.id}),
            post_data,
            follow=True,
        )

        self.assertRedirects(response, reverse("home"))

        response = self.client.post(
            reverse("questionnaires:questionnaire", kwargs={"questionnaire": self.active_questions.id}),
            post_data,
            follow=True,
        )

        self.assertContains(response, "Questionnaire already submitted.")

    def test_post_closed(self):

        response = self.client.post(
            reverse("questionnaires:questionnaire", kwargs={"questionnaire": self.closed_questions.id}),
            {},
            follow=True,
        )
        self.assertEquals(response.status_code, 404)

    def test_get_closed_questionnaire(self):
        response = self.client.get(
            reverse("questionnaires:questionnaire", kwargs={"questionnaire": self.closed_questions.id})
        )
        self.assertEquals(response.status_code, 404)

    def test_all_questionnaires_visible(self):
        response = self.client.get(reverse("questionnaires:overview"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.active_questions.title)
        self.assertContains(response, self.closed_questions.title)

    def test_warning_message_not_shown_when_user_is_in_team(self):
        response = self.client.get(
            reverse("questionnaires:questionnaire", kwargs={"questionnaire": self.active_questions.id})
        )
        self.assertNotContains(
            response,
            "This questionnaire contains questions about your team members, "
            "but you are either not in a project, or your project has no other peers.",
        )

    def test_warning_message_shown_when_user_is_alone(self):
        self.client.login(username="loner", password="123")
        response = self.client.get(
            reverse("questionnaires:questionnaire", kwargs={"questionnaire": self.active_questions.id})
        )
        self.assertContains(
            response,
            "This questionnaire contains questions about your team members, "
            "but you are either not in a project, or your project has no other peers.",
        )


class NoQuestionnairesTest(TestCase):
    def test_navbar_link_not_visible_with_no_questionnaires(self):
        response = self.client.get(reverse("home"))
        self.assertNotContains(response, "Questionnaires")
