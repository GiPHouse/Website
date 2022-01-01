from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.contrib.auth import get_user_model
from django.shortcuts import reverse
from django.test import Client, TestCase
from django.utils import timezone

from courses.models import Semester

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

        cls.semester = Semester.objects.get_or_create_current_semester()

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

        cls.closed_answer2 = Answer.objects.create(question=closed_question, submission=cls.submission)
        cls.closed_answer2.answer = 5

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

    def test_submission_csv_export(self):
        response = self.client.post(
            reverse("admin:questionnaires_questionnairesubmission_changelist"),
            {ACTION_CHECKBOX_NAME: [self.submission.pk], "action": "export_submissions", "index": 0},
        )

        self.assertContains(
            response, '"Questionnaire","Participant","Late","Question","Peer","Answer (as text)","Answer (as number)"'
        )

        self.assertContains(
            response,
            f'"{self.open_answer.submission.questionnaire}","{self.open_answer.submission.participant}",'
            f'"{self.open_answer.submission.late}","{self.open_answer.question.question}",'
            f'"{self.open_answer.peer}","{self.open_answer.answer}",""',
        )
        self.assertContains(
            response,
            f'"{self.closed_answer.submission.questionnaire}","{self.closed_answer.submission.participant}",'
            f'"{self.closed_answer.submission.late}","{self.closed_answer.question.question}",'
            f'"{self.closed_answer.peer}","{self.closed_answer.answer.get_value_display()}",'
            f'"{self.closed_answer.answer.value}"',
        )
        self.assertEqual(response.status_code, 200)

    def test_answer_csv_export(self):
        response = self.client.post(
            reverse("admin:questionnaires_answer_changelist"),
            {
                ACTION_CHECKBOX_NAME: [self.open_answer.pk, self.closed_answer.pk],
                "action": "export_answers",
                "index": 0,
            },
        )

        self.assertContains(
            response, '"Questionnaire","Participant","Late","Question","Peer","Answer (as text)","Answer (as number)"'
        )

        self.assertContains(
            response,
            f'"{self.open_answer.submission.questionnaire}","{self.open_answer.submission.participant}",'
            f'"{self.open_answer.submission.late}","{self.open_answer.question.question}",'
            f'"{self.open_answer.peer}","{self.open_answer.answer}",""',
        )
        self.assertContains(
            response,
            f'"{self.closed_answer.submission.questionnaire}","{self.closed_answer.submission.participant}",'
            f'"{self.closed_answer.submission.late}","{self.closed_answer.question.question}",'
            f'"{self.closed_answer.peer}","{self.closed_answer.answer.get_value_display()}",'
            f'"{self.closed_answer.answer.value}"',
        )
        self.assertEqual(response.status_code, 200)

    def test_duplicate_questionnaires(self):
        response = self.client.post(
            reverse("admin:questionnaires_questionnaire_changelist"),
            {ACTION_CHECKBOX_NAME: [self.active_questions.pk], "action": "duplicate_questionnaires", "index": 0},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

        self.assertEqual(Questionnaire.objects.count(), 2)

        new_questionnaire = Questionnaire.objects.last()

        self.assertEqual(new_questionnaire.title, self.active_questions.title)
        self.assertEqual(new_questionnaire.semester, Semester.objects.get_or_create_current_semester())
        self.assertEqual(new_questionnaire.question_set.count(), self.active_questions.question_set.count())

        for q1, q2 in zip(new_questionnaire.question_set.all(), self.active_questions.question_set.all()):
            self.assertEqual(q1, q2)

    def test_download_emails(self):
        response = self.client.post(
            reverse("admin:questionnaires_questionnaire_changelist"),
            {
                ACTION_CHECKBOX_NAME: [self.active_questions.pk],
                "action": "download_emails_for_employees_without_submission",
                "index": 0,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
