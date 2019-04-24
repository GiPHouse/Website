from courses.models import SeasonChoice, Semester

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from peer_review.models import Answer, Question, QuestionTypes, Questionnaire

from projects.models import Project


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
        cls.team = Project.objects.create(
            semester=Semester.objects.create(year=2019,
                                             season=SeasonChoice.spring.name,
                                             registration_start=timezone.now(),
                                             registration_end=timezone.now() + timezone.timedelta(days=60)),
            name="Test Project",
            description="Description",
        )
        cls.user = User.objects.create_user(
            username='myself',
            password='123'
        )
        cls.user.groups.add(cls.team)
        cls.user.save()
        cls.peer = User.objects.create_user(
            username='Jack',
        )
        cls.peer.groups.add(cls.team)
        cls.peer.save()
        cls.active_questions = Questionnaire.objects.create(
            title="An Active Questionnaire",
            available_from=timezone.now() - timezone.timedelta(days=2),
            available_until=timezone.now() + timezone.timedelta(days=1)
        )
        Question.objects.create(
            questionnaire=cls.active_questions,
            question='Open Question global',
            question_type=QuestionTypes.open_question.name,
            about_team_member=False
        )
        Question.objects.create(
            questionnaire=cls.active_questions,
            question='Closed Question global',
            question_type=QuestionTypes.agree_disagree.name,
            about_team_member=False
        )
        Question.objects.create(
            questionnaire=cls.active_questions,
            question='Open Question to peer',
            question_type=QuestionTypes.open_question.name,
            about_team_member=True
        )
        Question.objects.create(
            questionnaire=cls.active_questions,
            question='Closed Question to peer',
            question_type=QuestionTypes.agree_disagree.name,
            about_team_member=True
        )
        Question.objects.create(
            questionnaire=cls.active_questions,
            question='Closed Question to peer',
            question_type=QuestionTypes.poor_good.name,
            about_team_member=True
        )
        cls.questions = Question.objects.filter(questionnaire=cls.active_questions)
        cls.inactive_questions = Questionnaire.objects.create(
            title="An Inactive Questionnaire",
            available_from=timezone.now() - timezone.timedelta(days=2),
            available_until=timezone.now() - timezone.timedelta(days=1)
        )
        Question.objects.create(
            questionnaire=cls.inactive_questions,
            question='Question for an inactive set',
            question_type=QuestionTypes.poor_good.name,
            about_team_member=False
        )

    def setUp(self):
        self.client = Client()
        self.client.login(username='myself', password='123')

    def test_str_question(self):
        question = self.questions[0]
        str_actual = 'Open Question global'
        self.assertEqual(str(question), str_actual)

    def test_str_answer(self):
        a = "Something"
        answer = Answer.objects.create(
            participant=self.user,
            peer=self.peer,
            question=self.questions[0],
            answer=a,
        )
        str_actual = '(myself about Jack) Open Question global:  answer Something'
        self.assertEqual(str(answer), str_actual)

    def test_get_form(self):
        """
        Test GET request to form view
        """
        response = self.client.get(reverse('peer_review:answer', args=(self.active_questions.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_post_form(self):
        """
        Test POST request to form view
        """
        peers = User.objects.exclude(pk=self.user.pk)
        post = generate_post_data(self.questions, peers)
        response = self.client.post(
            reverse('peer_review:answer', args=(self.active_questions.pk,)),
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

    def test_only_active_questionnaires_visible(self):
        """
        Test overview page to check if only active sets are visible
        """
        response = self.client.get(reverse('peer_review:overview'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'An Active Questionnaire')
        self.assertNotContains(response, 'An Inactive Questionnaire')

    def test_navbar_link_goes_to_only_questionnaire_if_available(self):
        response = self.client.get(reverse('home'))
        self.assertInHTML(
            f'<a href="/review/{self.active_questions.id}" target="_self" class="nav-link">Peer Review</a>',
            response.rendered_content
        )

    def test_navbar_overview_link_with_multiple_questionnaires(self):
        Questionnaire.objects.create(
            title="Another Active Questionnaire",
            available_from=timezone.now() - timezone.timedelta(days=2),
            available_until=timezone.now() + timezone.timedelta(days=1)
        )
        response = self.client.get(reverse('home'))
        self.assertInHTML(
            f'<a class="nav-link" target="_self" href="/review/">Peer Review</a>',
            response.rendered_content
        )


class NoQuestionnairesTest(TestCase):
    def test_navbar_link_not_visible_with_no_questionnaires(self):
        response = self.client.get(reverse('home'))
        self.assertNotContains(
            response,
            'Peer Review',
        )
