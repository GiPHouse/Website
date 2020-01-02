from django.contrib.auth import get_user_model
from django.shortcuts import reverse
from django.test import Client, TestCase
from django.utils import timezone

from courses.models import Semester, current_season

from projects.models import Project

from questionnaires.filters import (
    AnswerAdminParticipantFilter,
    AnswerAdminProjectFilter,
    AnswerAdminQuestionnaireFilter,
    AnswerAdminSemesterFilter,
    SubmissionAdminPeerFilter,
    SubmissionAdminProjectFilter,
    SubmissionAdminSemesterFilter,
)
from questionnaires.models import Answer, Question, Questionnaire, QuestionnaireSubmission

from registrations.models import Employee

User: Employee = get_user_model()


class QuestionnaireTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_password = "hunter2"
        cls.admin = User.objects.create_superuser(github_id=0, github_username="test")

        cls.semester = Semester.objects.create(
            year=2019,
            season=current_season(),
            registration_start=timezone.now(),
            registration_end=timezone.now() + timezone.timedelta(days=60),
        )

        cls.user = User.objects.create_user(github_id=1, github_username="test2")

        cls.project = Project.objects.create(semester=cls.semester, name="Project")

        peer = User.objects.create_user(github_id=2, github_username="test3")

        cls.active_questions = Questionnaire.objects.create(
            semester=cls.semester,
            title="An Active Questionnaire",
            available_from=timezone.now() - timezone.timedelta(days=2),
            available_until_soft=timezone.now() + timezone.timedelta(days=1),
            available_until_hard=timezone.now() + timezone.timedelta(days=1),
        )

        open_question = Question.objects.create(
            questionnaire=cls.active_questions, question="OQ", question_type=Question.OPEN, about_team_member=True
        )

        closed_question = Question.objects.create(
            questionnaire=cls.active_questions, question="CQ", question_type=Question.QUALITY, about_team_member=True
        )

        Question.objects.create(
            questionnaire=cls.active_questions, question="CQ2", question_type=Question.QUALITY, about_team_member=False
        )

        cls.submission = QuestionnaireSubmission.objects.create(
            questionnaire=cls.active_questions, participant=cls.user
        )

        cls.open_answer = Answer.objects.create(question=open_question, submission=cls.submission, peer=peer)
        cls.open_answer.answer = "Lorem ipsum dolor sit amet, consectetur adipiscing elit."

        cls.closed_answer = Answer.objects.create(question=closed_question, submission=cls.submission, peer=peer)
        cls.closed_answer.answer = 1

        Answer.objects.create(question=closed_question, submission=cls.submission)

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.admin)

    def test_get_submission_changelist(self):
        response = self.client.get(reverse("admin:questionnaires_questionnairesubmission_changelist"), follow=True)
        self.assertEqual(response.status_code, 200)

    def test_get_submission_changelist_semesterfilter(self):
        response = self.client.get(
            reverse("admin:questionnaires_questionnairesubmission_changelist"),
            data={
                f"{SubmissionAdminSemesterFilter.field_name}__"
                f"{SubmissionAdminSemesterFilter.field_pk}__exact": self.semester.id
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

    def test_get_submission_changelist_projectfilter(self):
        response = self.client.get(
            reverse("admin:questionnaires_questionnairesubmission_changelist"),
            data={
                f"{SubmissionAdminProjectFilter.field_name}__"
                f"{SubmissionAdminProjectFilter.field_pk}__exact": self.project.id
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

    def test_get_submission_changelist_peerfilter(self):
        response = self.client.get(
            reverse("admin:questionnaires_questionnairesubmission_changelist"),
            data={
                f"{SubmissionAdminPeerFilter.field_name}__{SubmissionAdminPeerFilter.field_pk}__exact": self.user.id
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

    def test_view_submission_object(self):
        response = self.client.get(
            reverse("admin:questionnaires_questionnairesubmission_change", kwargs={"object_id": self.submission.id}),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

    def test_get_answer_changelist(self):
        response = self.client.get(reverse("admin:questionnaires_answer_changelist"), follow=True)
        self.assertEqual(response.status_code, 200)

    def test_get_answer_changelist_questionnairefilter(self):
        response = self.client.get(
            reverse("admin:questionnaires_answer_changelist"),
            data={
                f"{AnswerAdminQuestionnaireFilter.field_name}__"
                f"{AnswerAdminQuestionnaireFilter.field_pk}__exact": self.active_questions.id
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

    def test_get_answer_changelist_projectfilter(self):
        response = self.client.get(
            reverse("admin:questionnaires_answer_changelist"),
            data={
                f"{AnswerAdminProjectFilter.field_name}__"
                f"{AnswerAdminProjectFilter.field_pk}__exact": self.project.id
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

    def test_get_answer_changelist_participantfilter(self):
        response = self.client.get(
            reverse("admin:questionnaires_answer_changelist"),
            data={
                f"{AnswerAdminParticipantFilter.field_name}__"
                f"{AnswerAdminParticipantFilter.field_pk}__exact": self.user.id
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

    def test_get_answer_changelist_semesterfilter(self):
        response = self.client.get(
            reverse("admin:questionnaires_answer_changelist"),
            data={
                f"{AnswerAdminSemesterFilter.field_name}__"
                f"{AnswerAdminSemesterFilter.field_pk}__exact": self.semester.id
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
