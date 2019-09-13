from django.contrib.auth import get_user_model
from django.contrib.auth.models import User as DjangoUser
from django.shortcuts import reverse
from django.test import Client, TestCase
from django.utils import timezone

from freezegun import freeze_time

from courses.models import Semester

from projects.models import Project

from questionnaires.filters import (
    AnswerAdminParticipantFilter,
    AnswerAdminProjectFilter,
    AnswerAdminQuestionnaireFilter,
    AnswerAdminSemesterFilter,
    AnswerAdminValueFilter,
    SubmissionAdminAverageFilter,
    SubmissionAdminPeerFilter,
    SubmissionAdminProjectFilter,
    SubmissionAdminSemesterFilter,
)
from questionnaires.models import Answer, Question, Questionnaire, QuestionnaireSubmission

User: DjangoUser = get_user_model()


class QuestionnaireTest(TestCase):

    @classmethod
    @freeze_time("2019-01-01")
    def setUpTestData(cls):
        cls.admin_password = 'hunter2'
        cls.admin = User.objects.create_superuser(
            username='admin',
            email='',
            password=cls.admin_password)

        cls.semester = Semester.objects.create(
            year=2019,
            season=Semester.SPRING,
            registration_start=timezone.now(),
            registration_end=timezone.now() + timezone.timedelta(days=60)
        )

        cls.user = User.objects.create_user(
            username='user',
            password='123',
            first_name='User',
            last_name='Name',
        )

        cls.project = Project.objects.create(
            semester=cls.semester,
            name='Project'
        )

        peer = User.objects.create_user(
            username='peer',
            password='123',
            first_name='Peer',
            last_name='Name',
        )

        cls.active_questions = Questionnaire.objects.create(
            semester=cls.semester,
            title="An Active Questionnaire",
            available_from=timezone.now() - timezone.timedelta(days=2),
            available_until_soft=timezone.now() + timezone.timedelta(days=1),
            available_until_hard=timezone.now() + timezone.timedelta(days=1),
        )

        open_question = Question.objects.create(
            questionnaire=cls.active_questions,
            question='OQ',
            question_type=Question.OPEN,
            about_team_member=True
        )

        closed_question = Question.objects.create(
            questionnaire=cls.active_questions,
            question='CQ',
            question_type=Question.QUALITY,
            about_team_member=True
        )

        Question.objects.create(
            questionnaire=cls.active_questions,
            question='CQ2',
            question_type=Question.QUALITY,
            about_team_member=False
        )

        cls.submission = QuestionnaireSubmission.objects.create(
            questionnaire=cls.active_questions,
            participant=cls.user,
        )

        cls.open_answer = Answer.objects.create(
            question=open_question,
            submission=cls.submission,
            peer=peer,
        )
        cls.open_answer.answer = "Lorem ipsum dolor sit amet, consectetur adipiscing elit."

        cls.closed_answer = Answer.objects.create(
            question=closed_question,
            submission=cls.submission,
            peer=peer,
        )
        cls.closed_answer.answer = 1

        Answer.objects.create(
            question=closed_question,
            submission=cls.submission,
        )

    def setUp(self):
        self.client = Client()
        self.client.login(username=self.admin.username, password=self.admin_password)

    @freeze_time("2019-01-01")
    def test_get_submission_changelist(self):
        response = self.client.get(
            reverse('admin:questionnaires_questionnairesubmission_changelist'),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

    @freeze_time("2019-01-01")
    def test_get_submission_changelist_averagefilter(self):
        response = self.client.get(
            reverse('admin:questionnaires_questionnairesubmission_changelist'),
            data={
                SubmissionAdminAverageFilter.parameter_name: self.closed_answer.answer.value + 0.5,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

    @freeze_time("2019-01-01")
    def test_get_submission_changelist_averagefilter_below(self):
        response = self.client.get(
            reverse('admin:questionnaires_questionnairesubmission_changelist'),
            data={
                SubmissionAdminAverageFilter.parameter_name: self.closed_answer.answer.value - 0.5,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

    @freeze_time("2019-01-01")
    def test_get_submission_changelist_semesterfilter(self):
        response = self.client.get(
            reverse('admin:questionnaires_questionnairesubmission_changelist'),
            data={
                f'{SubmissionAdminSemesterFilter.field_name}__id__exact': self.semester.id,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

    @freeze_time("2019-01-01")
    def test_get_submission_changelist_projectfilter(self):
        response = self.client.get(
            reverse('admin:questionnaires_questionnairesubmission_changelist'),
            data={
                SubmissionAdminProjectFilter.parameter_name: self.project.id,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

    @freeze_time("2019-01-01")
    def test_get_submission_changelist_peerfilter(self):
        response = self.client.get(
            reverse('admin:questionnaires_questionnairesubmission_changelist'),
            data={
                f'{SubmissionAdminPeerFilter.field_name}__id__exact': self.user.id,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

    @freeze_time("2019-01-01")
    def test_view_submission_object(self):
        response = self.client.get(
            reverse('admin:questionnaires_questionnairesubmission_change', kwargs={'object_id': self.submission.id}),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

    @freeze_time("2019-01-01")
    def test_get_answer_changelist(self):
        response = self.client.get(
            reverse('admin:questionnaires_answer_changelist'),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

    @freeze_time("2019-01-01")
    def test_get_answer_changelist_questionnairefilter(self):
        response = self.client.get(
            reverse('admin:questionnaires_answer_changelist'),
            data={
                f'{AnswerAdminQuestionnaireFilter.field_name}__id__exact': self.active_questions.id,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

    @freeze_time("2019-01-01")
    def test_get_answer_changelist_projectfilter(self):
        response = self.client.get(
            reverse('admin:questionnaires_answer_changelist'),
            data={
                AnswerAdminProjectFilter.parameter_name: self.project.id,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

    @freeze_time("2019-01-01")
    def test_get_answer_changelist_participantfilter(self):
        response = self.client.get(
            reverse('admin:questionnaires_answer_changelist'),
            data={
                f'{AnswerAdminParticipantFilter.field_name}__id__exact': self.user.id,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

    @freeze_time("2019-01-01")
    def test_get_answer_changelist_valuefilter(self):
        response = self.client.get(
            reverse('admin:questionnaires_answer_changelist'),
            data={
                AnswerAdminValueFilter.parameter_name: self.closed_answer.answer.value + 0.5,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

    @freeze_time("2019-01-01")
    def test_get_answer_changelist_semesterfilter(self):
        response = self.client.get(
            reverse('admin:questionnaires_answer_changelist'),
            data={
                f'{AnswerAdminSemesterFilter.field_name}__id__exact': self.semester.id,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
