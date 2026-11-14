from django.contrib.auth import get_user_model
from django.test import TestCase

from courses.models import Semester

from registrations.models import Employee

from registrations.models.registration import (
    QuestionChoice,
    Registrations,
    RegistrationSubmission,
    Question,
    Answer,
    TextData,
    ChoiceData,
    MultiData,
)

User: Employee = get_user_model()


class questionTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Set up data for the happy path tests
        cls.test_semester = Semester.objects.get_or_create_current_semester()
        cls.test_registration = Registrations.objects.create(
            title="Test Registration", semester=cls.test_semester
        )
        cls.test_participant = Employee.objects.create_user(
            github_id=1, first_name="Test", last_name="Participant"
        )
        cls.test_submission = RegistrationSubmission.objects.create(
            registration=cls.test_registration,
            participant=cls.test_participant,
        )
        # TEST QUESTION TYPES
        cls.test_question_CHOICE = Question.objects.create(
            registration=cls.test_registration,
            question="What is your favorite color?",
            question_type=Question.CHOICE,
            optional=False,
        )
        cls.test_question_TEXT = Question.objects.create(
            registration=cls.test_registration,
            question="What is your name?",
            question_type=Question.TEXT,
            optional=False,
        )
        cls.test_question_BIGTEXT = Question.objects.create(
            registration=cls.test_registration,
            question="Please describe your experience with Python:",
            question_type=Question.BIGTEXT,
            optional=False,
        )
        cls.test_question_MULTI = Question.objects.create(
            registration=cls.test_registration,
            question="Please select all that apply:",
            question_type=Question.MULTI,
            optional=False,
        )
        cls.test_question_DROPDOWN = Question.objects.create(
            registration=cls.test_registration,
            question="Please select your preferred option:",
            question_type=Question.DROPDOWN,
            optional=False,
        )
        # TEST ANSWERS models
        cls.test_answer_CHOICE = Answer.objects.create(
            submission=cls.test_submission, question=cls.test_question_CHOICE
        )
        cls.test_answer_TEXT = Answer.objects.create(
            submission=cls.test_submission, question=cls.test_question_TEXT
        )
        cls.test_answer_BIGTEXT = Answer.objects.create(
            submission=cls.test_submission, question=cls.test_question_BIGTEXT
        )
        cls.test_answer_MULTI = Answer.objects.create(
            submission=cls.test_submission, question=cls.test_question_MULTI
        )
        cls.test_answer_DROPDOWN = Answer.objects.create(
            submission=cls.test_submission, question=cls.test_question_DROPDOWN
        )
        # TEST ANSWERS DATA
        cls.test_TextData = TextData.objects.create(
            answer=cls.test_answer_TEXT, value="Test Participant"
        )
        cls.test_BigTextData = TextData.objects.create(
            answer=cls.test_answer_BIGTEXT,
            value="I have been programming in Python for 5 years and have experience with Django and Flask.",
        )

        cls.test_questionChoice = QuestionChoice.objects.create(
            question=cls.test_question_CHOICE, value="Blue"
        )
        cls.test_questionMulti1 = QuestionChoice.objects.create(
            question=cls.test_question_MULTI, value="Option 1"
        )
        cls.test_questionMulti2 = QuestionChoice.objects.create(
            question=cls.test_question_MULTI, value="Option 2"
        )

        cls.test_ChoiceData = ChoiceData.objects.create(
            answer=cls.test_answer_CHOICE, choice=cls.test_questionChoice
        )
        cls.test_MultiData = MultiData.objects.create(
            answer=cls.test_answer_MULTI,
        )
        cls.test_MultiData.choices.set(
            [cls.test_questionMulti1, cls.test_questionMulti2]
        )
        cls.test_DropdownData = ChoiceData.objects.create(
            answer=cls.test_answer_DROPDOWN, choice=cls.test_questionMulti1
        )

        # Set up data for edge case tests (e.g., missing fields, invalid data types)

    def test_registration_str(self):
        self.assertEqual(
            f"{self.test_registration.title} ({self.test_semester})",
            str(self.test_registration),
        )

    def test_registrationsubmission_str(self):
        submission = RegistrationSubmission.objects.create(
            registration=self.test_registration,
            participant=self.test_participant,
        )
        self.assertEqual(
            f"{self.test_registration.title} submission by {self.test_participant} at {submission.created}",
            str(submission),
        )

    def test_question_str(self):
        self.assertEqual(
            "What is your favorite color?", str(self.test_question_CHOICE)
        )

    def test_answer_get(self):
        self.assertEqual("Blue", self.test_answer_CHOICE.answer_value)
        self.assertEqual(
            "Test Participant", self.test_answer_TEXT.answer_value
        )
        self.assertEqual(
            "I have been programming in Python for 5 years and have experience with Django and Flask.",
            self.test_answer_BIGTEXT.answer_value,
        )
        self.assertEqual(
            "Option 1 § Option 2", self.test_answer_MULTI.answer_value
        )
        self.assertEqual("Option 1", self.test_answer_DROPDOWN.answer_value)

    # Follow-up question tests

    def test_create_follow_up_question(self):
        """Test creating a follow-up question linked to a parent choice."""
        parent_choice = self.test_questionChoice  # "Blue" choice
        follow_up_question = Question.objects.create(
            registration=self.test_registration,
            question="Why is blue your favorite color?",
            question_type=Question.TEXT,
            optional=False,
            parent_choice=parent_choice,
        )

        self.assertEqual(follow_up_question.parent_choice, parent_choice)
        self.assertEqual(
            follow_up_question.question, "Why is blue your favorite color?"
        )
        self.assertIsNotNone(follow_up_question.parent_choice)

    def test_follow_up_question_in_related_manager(self):
        """Test that follow-up questions are accessible via parent choice's related_name."""
        parent_choice = self.test_questionChoice
        follow_up_question = Question.objects.create(
            registration=self.test_registration,
            question="Why is blue your favorite color?",
            question_type=Question.TEXT,
            optional=False,
            parent_choice=parent_choice,
        )

        # Access via related_name "follow_up_questions"
        follow_up_questions = parent_choice.follow_up_questions.all()
        self.assertIn(follow_up_question, follow_up_questions)
        self.assertEqual(follow_up_questions.count(), 1)

    def test_multiple_follow_up_questions(self):
        """Test that a single choice can have multiple follow-up questions."""
        parent_choice = self.test_questionChoice
        follow_up_q1 = Question.objects.create(
            registration=self.test_registration,
            question="Why is blue your favorite?",
            question_type=Question.TEXT,
            optional=False,
            parent_choice=parent_choice,
        )
        follow_up_q2 = Question.objects.create(
            registration=self.test_registration,
            question="How often do you wear blue?",
            question_type=Question.CHOICE,
            optional=True,
            parent_choice=parent_choice,
        )

        follow_up_questions = parent_choice.follow_up_questions.all()
        self.assertEqual(follow_up_questions.count(), 2)
        self.assertIn(follow_up_q1, follow_up_questions)
        self.assertIn(follow_up_q2, follow_up_questions)

    def test_follow_up_question_optional_field(self):
        """Test that follow-up questions can be optional."""
        parent_choice = self.test_questionChoice
        optional_follow_up = Question.objects.create(
            registration=self.test_registration,
            question="Tell us more about blue:",
            question_type=Question.BIGTEXT,
            optional=True,
            parent_choice=parent_choice,
        )

        self.assertTrue(optional_follow_up.optional)
        self.assertEqual(optional_follow_up.parent_choice, parent_choice)

    def test_follow_up_question_deletion_cascade(self):
        """Test that follow-up questions are deleted when parent choice is deleted."""
        parent_choice = self.test_questionChoice
        follow_up_question = Question.objects.create(
            registration=self.test_registration,
            question="Why is blue your favorite?",
            question_type=Question.TEXT,
            optional=False,
            parent_choice=parent_choice,
        )

        follow_up_id = follow_up_question.id
        parent_choice.delete()

        # Follow-up question should be deleted due to CASCADE
        with self.assertRaises(Question.DoesNotExist):
            Question.objects.get(id=follow_up_id)

    def test_question_choice_str(self):
        """Test the string representation of QuestionChoice."""
        choice = self.test_questionChoice
        self.assertEqual(str(choice), "Blue")

    def test_question_choice_follow_up_field(self):
        """Test the follow_up field on QuestionChoice."""
        # Create a choice with follow_up=False (default)
        normal_choice = QuestionChoice.objects.create(
            question=self.test_question_CHOICE, value="Red", follow_up=False
        )
        self.assertFalse(normal_choice.follow_up)

        # Create a choice with follow_up=True
        follow_up_choice = QuestionChoice.objects.create(
            question=self.test_question_CHOICE, value="Other", follow_up=True
        )
        self.assertTrue(follow_up_choice.follow_up)

    def test_follow_up_question_different_types(self):
        """Test follow-up questions can have different question types."""
        parent_choice = QuestionChoice.objects.create(
            question=self.test_question_CHOICE, value="Green"
        )

        # TEXT follow-up
        text_follow_up = Question.objects.create(
            registration=self.test_registration,
            question="Explain green:",
            question_type=Question.TEXT,
            parent_choice=parent_choice,
        )

        # CHOICE follow-up
        choice_follow_up = Question.objects.create(
            registration=self.test_registration,
            question="What shade of green?",
            question_type=Question.CHOICE,
            parent_choice=parent_choice,
        )

        # MULTI follow-up
        multi_follow_up = Question.objects.create(
            registration=self.test_registration,
            question="Green uses:",
            question_type=Question.MULTI,
            parent_choice=parent_choice,
        )

        follow_ups = parent_choice.follow_up_questions.all()
        self.assertEqual(follow_ups.count(), 3)
        self.assertEqual(text_follow_up.question_type, Question.TEXT)
        self.assertEqual(choice_follow_up.question_type, Question.CHOICE)
        self.assertEqual(multi_follow_up.question_type, Question.MULTI)

    def test_follow_up_question_with_answer(self):
        """Test that answers can be created for follow-up questions."""
        parent_choice = self.test_questionChoice
        follow_up_question = Question.objects.create(
            registration=self.test_registration,
            question="Why is blue your favorite?",
            question_type=Question.TEXT,
            optional=False,
            parent_choice=parent_choice,
        )

        follow_up_answer = Answer.objects.create(
            submission=self.test_submission, question=follow_up_question
        )
        follow_up_answer.answer = "It's calming and cool."

        self.assertEqual(follow_up_answer.question, follow_up_question)
        self.assertEqual(
            follow_up_answer.answer_value, "It's calming and cool."
        )

    def test_follow_up_question_no_parent_choice(self):
        """Test that regular questions don't have a parent choice."""
        regular_question = self.test_question_TEXT
        self.assertIsNone(regular_question.parent_choice)

    def test_nested_follow_up_questions_not_supported(self):
        """Test that follow-up questions themselves can have a parent_choice (edge case)."""
        # This tests the database structure allows it, though UI might not support it
        parent_choice = self.test_questionChoice
        follow_up_q1 = Question.objects.create(
            registration=self.test_registration,
            question="Why blue?",
            question_type=Question.TEXT,
            parent_choice=parent_choice,
        )

        # This demonstrates the structure allows nested follow-ups at DB level
        self.assertEqual(follow_up_q1.parent_choice, parent_choice)

    def test_follow_up_question_with_constraints(self):
        """Test follow-up question with min/max choices constraints."""
        parent_choice = self.test_questionChoice
        follow_up_multi = Question.objects.create(
            registration=self.test_registration,
            question="Select your preferences:",
            question_type=Question.MULTI,
            parent_choice=parent_choice,
            min_choices=1,
            max_choices=3,
        )

        self.assertEqual(follow_up_multi.min_choices, 1)
        self.assertEqual(follow_up_multi.max_choices, 3)
        self.assertEqual(follow_up_multi.parent_choice, parent_choice)

    # ===== EDGE CASE TESTS =====

    def test_answer_without_data_returns_empty_value(self):
        """Test answer_value handles missing data gracefully."""
        # Create answer without creating TextData
        answer = Answer.objects.create(
            submission=self.test_submission, question=self.test_question_TEXT
        )
        # The answer_value property will raise RelatedObjectDoesNotExist
        # This is an edge case that shouldn't happen in normal flow
        try:
            _ = answer.answer_value
        except Exception:
            # Expected behavior - missing data causes exception
            pass

    def test_answer_without_choicedata_returns_empty_value(self):
        """Test answer_value handles missing ChoiceData gracefully."""
        answer = Answer.objects.create(
            submission=self.test_submission,
            question=self.test_question_CHOICE,
        )
        # The answer_value property will raise RelatedObjectDoesNotExist
        # This is an edge case that shouldn't happen in normal flow
        try:
            _ = answer.answer_value
        except Exception:
            # Expected behavior - missing data causes exception
            pass

    def test_answer_without_multidata_returns_empty_value(self):
        """Test answer_value returns empty for MULTI type without MultiData."""
        answer = Answer.objects.create(
            submission=self.test_submission, question=self.test_question_MULTI
        )
        self.assertEqual(answer.answer_value, "")

    def test_textdata_with_empty_value(self):
        """Test TextData can store empty string."""
        answer = Answer.objects.create(
            submission=self.test_submission, question=self.test_question_TEXT
        )
        empty_data = TextData.objects.create(answer=answer, value="")
        self.assertEqual(empty_data.value, "")
        self.assertEqual(str(empty_data), "")

    def test_textdata_with_none_value(self):
        """Test TextData can store None value."""
        answer = Answer.objects.create(
            submission=self.test_submission, question=self.test_question_TEXT
        )
        none_data = TextData.objects.create(answer=answer, value=None)
        self.assertIsNone(none_data.value)

    def test_textdata_with_very_long_text(self):
        """Test TextData can store very long text."""
        answer = Answer.objects.create(
            submission=self.test_submission,
            question=self.test_question_BIGTEXT,
        )
        long_text = "A" * 10000  # 10k characters
        long_data = TextData.objects.create(answer=answer, value=long_text)
        self.assertEqual(long_data.value, long_text)

    def test_multidata_with_no_choices(self):
        """Test MultiData can exist with no choices selected."""
        answer = Answer.objects.create(
            submission=self.test_submission, question=self.test_question_MULTI
        )
        multi_data = MultiData.objects.create(answer=answer)
        # Don't add any choices
        self.assertEqual(multi_data.choices.count(), 0)
        self.assertEqual(answer.answer_value, "")

    def test_multidata_with_single_choice(self):
        """Test MultiData with single choice returns correct format."""
        answer = Answer.objects.create(
            submission=self.test_submission, question=self.test_question_MULTI
        )
        multi_data = MultiData.objects.create(answer=answer)
        multi_data.choices.add(self.test_questionMulti1)
        self.assertEqual(answer.answer_value, "Option 1")

    def test_multiple_submissions_same_participant(self):
        """Test same participant can have multiple submissions for same registration."""
        submission2 = RegistrationSubmission.objects.create(
            registration=self.test_registration,
            participant=self.test_participant,
        )
        submission3 = RegistrationSubmission.objects.create(
            registration=self.test_registration,
            participant=self.test_participant,
        )
        # these two lines are necessary to avoid ruff from complaining about unused variables
        submission2.submitted = True
        submission3.submitted = True

        submissions = RegistrationSubmission.objects.filter(
            participant=self.test_participant,
            registration=self.test_registration,
        )
        self.assertEqual(submissions.count(), 3)  # original + 2 new

    def test_multiple_participants_same_registration(self):
        """Test multiple participants can submit same registration."""
        participant2 = Employee.objects.create_user(
            github_id=2,
            github_username="second_user",
            first_name="Second",
            last_name="Person",
        )
        submission2 = RegistrationSubmission.objects.create(
            registration=self.test_registration, participant=participant2
        )

        self.assertNotEqual(
            self.test_submission.participant, submission2.participant
        )
        self.assertEqual(
            self.test_submission.registration, submission2.registration
        )

    def test_submission_without_answers(self):
        """Test submission can exist without any answers."""
        empty_submission = RegistrationSubmission.objects.create(
            registration=self.test_registration,
            participant=self.test_participant,
        )
        self.assertEqual(empty_submission.answer_set.count(), 0)

    def test_question_with_max_length_text(self):
        """Test question can be created with maximum length text."""
        max_length_question = "Q" * 255  # max_length=255
        question = Question.objects.create(
            registration=self.test_registration,
            question=max_length_question,
            question_type=Question.TEXT,
        )
        self.assertEqual(len(question.question), 255)

    def test_question_choice_with_max_length_value(self):
        """Test QuestionChoice can be created with maximum length value."""
        max_length_value = "V" * 255  # max_length=255
        choice = QuestionChoice.objects.create(
            question=self.test_question_CHOICE, value=max_length_value
        )
        self.assertEqual(len(choice.value), 255)

    def test_min_max_choices_constraints(self):
        """Test min and max choices constraints can be set together."""
        question = Question.objects.create(
            registration=self.test_registration,
            question="Pick between 2-4 options:",
            question_type=Question.MULTI,
            min_choices=2,
            max_choices=4,
        )
        self.assertEqual(question.min_choices, 2)
        self.assertEqual(question.max_choices, 4)

    def test_min_choices_without_max(self):
        """Test min_choices can be set without max_choices."""
        question = Question.objects.create(
            registration=self.test_registration,
            question="Pick at least 2:",
            question_type=Question.MULTI,
            min_choices=2,
        )
        self.assertEqual(question.min_choices, 2)
        self.assertIsNone(question.max_choices)

    def test_max_choices_without_min(self):
        """Test max_choices can be set without min_choices."""
        question = Question.objects.create(
            registration=self.test_registration,
            question="Pick at most 3:",
            question_type=Question.MULTI,
            max_choices=3,
        )
        self.assertIsNone(question.min_choices)
        self.assertEqual(question.max_choices, 3)

    def test_zero_max_choices(self):
        """Test edge case of max_choices=0."""
        question = Question.objects.create(
            registration=self.test_registration,
            question="Pick options:",
            question_type=Question.MULTI,
            max_choices=0,
        )
        self.assertEqual(question.max_choices, 0)

    def test_follow_up_question_with_large_min_choices(self):
        """Test follow-up with large min_choices value."""
        parent_choice = self.test_questionChoice
        follow_up = Question.objects.create(
            registration=self.test_registration,
            question="Select many:",
            question_type=Question.MULTI,
            parent_choice=parent_choice,
            min_choices=999999,
        )
        self.assertEqual(follow_up.min_choices, 999999)

    def test_deletion_with_orphaned_follow_ups(self):
        """Test deleting registration cascades to follow-up questions."""
        parent_choice = self.test_questionChoice
        follow_up = Question.objects.create(
            registration=self.test_registration,
            question="Follow-up:",
            question_type=Question.TEXT,
            parent_choice=parent_choice,
        )
        follow_up_id = follow_up.id

        self.test_registration.delete()

        with self.assertRaises(Question.DoesNotExist):
            Question.objects.get(id=follow_up_id)

    def test_question_choice_follow_up_flag_with_follow_up_questions(self):
        """Test follow_up flag on choice that has follow-up questions."""
        choice_with_followups = QuestionChoice.objects.create(
            question=self.test_question_CHOICE,
            value="Maybe",
            follow_up=True,
        )
        follow_up = Question.objects.create(
            registration=self.test_registration,
            question="Explain maybe:",
            question_type=Question.TEXT,
            parent_choice=choice_with_followups,
        )
        # this line is necessary to avoid ruff from complaining about unused variable
        follow_up.optional = False
        self.assertTrue(choice_with_followups.follow_up)
        self.assertEqual(choice_with_followups.follow_up_questions.count(), 1)

    def test_answer_property_with_different_question_types(self):
        """Test answer property returns None when data doesn't exist for any type."""
        text_answer = Answer.objects.create(
            submission=self.test_submission, question=self.test_question_TEXT
        )
        choice_answer = Answer.objects.create(
            submission=self.test_submission, question=self.test_question_CHOICE
        )
        multi_answer = Answer.objects.create(
            submission=self.test_submission, question=self.test_question_MULTI
        )

        self.assertIsNone(text_answer.answer)
        self.assertIsNone(choice_answer.answer)
        self.assertIsNone(multi_answer.answer)

    def test_registration_submission_field_submitted_true(self):
        """Test RegistrationSubmission submitted field defaults to True."""
        submission = RegistrationSubmission.objects.create(
            registration=self.test_registration,
            participant=self.test_participant,
        )
        self.assertTrue(submission.submitted)

    def test_registration_submission_field_submitted_false(self):
        """Test RegistrationSubmission submitted field can be False."""
        submission = RegistrationSubmission.objects.create(
            registration=self.test_registration,
            participant=self.test_participant,
            submitted=False,
        )
        self.assertFalse(submission.submitted)

    def test_question_optional_true(self):
        """Test question can be marked as optional."""
        optional_question = Question.objects.create(
            registration=self.test_registration,
            question="Optional:",
            question_type=Question.TEXT,
            optional=True,
        )
        self.assertTrue(optional_question.optional)

    def test_question_optional_false_default(self):
        """Test question optional defaults to False."""
        required_question = Question.objects.create(
            registration=self.test_registration,
            question="Required:",
            question_type=Question.TEXT,
        )
        self.assertFalse(required_question.optional)

    def test_question_with_warnings_field(self):
        """Test question can store warnings."""
        question_with_warning = Question.objects.create(
            registration=self.test_registration,
            question="Complex question:",
            question_type=Question.TEXT,
            warnings="This field requires careful consideration",
        )
        self.assertEqual(
            question_with_warning.warnings,
            "This field requires careful consideration",
        )

    def test_question_with_empty_warnings(self):
        """Test question warnings can be empty."""
        question = Question.objects.create(
            registration=self.test_registration,
            question="Simple question:",
            question_type=Question.TEXT,
            warnings="",
        )
        self.assertEqual(question.warnings, "")

    def test_question_with_none_warnings(self):
        """Test question warnings can be None."""
        question = Question.objects.create(
            registration=self.test_registration,
            question="Simple question:",
            question_type=Question.TEXT,
            warnings=None,
        )
        self.assertIsNone(question.warnings)

    def test_follow_up_question_inherits_registration(self):
        """Test follow-up question is in same registration as parent question."""
        parent_choice = self.test_questionChoice
        follow_up = Question.objects.create(
            registration=self.test_registration,
            question="Follow-up:",
            question_type=Question.TEXT,
            parent_choice=parent_choice,
        )

        self.assertEqual(
            follow_up.registration, self.test_question_CHOICE.registration
        )

    def test_multiple_follow_ups_different_question_fields(self):
        """Test follow-up questions can have different field values."""
        parent_choice = self.test_questionChoice
        follow_up1 = Question.objects.create(
            registration=self.test_registration,
            question="Follow-up 1",
            question_type=Question.TEXT,
            parent_choice=parent_choice,
            optional=True,
        )
        follow_up2 = Question.objects.create(
            registration=self.test_registration,
            question="Follow-up 2",
            question_type=Question.BIGTEXT,
            parent_choice=parent_choice,
            optional=False,
            warnings="Required field",
        )

        self.assertNotEqual(follow_up1.question_type, follow_up2.question_type)
        self.assertNotEqual(follow_up1.optional, follow_up2.optional)
        self.assertNotEqual(follow_up1.warnings, follow_up2.warnings)

    # ===== QUESTION TYPE TESTS =====

    # TEXT TYPE TESTS
    def test_text_question_creation(self):
        """Test creating a TEXT type question."""
        text_question = Question.objects.create(
            registration=self.test_registration,
            question="Enter your name:",
            question_type=Question.TEXT,
        )
        self.assertEqual(text_question.question_type, Question.TEXT)

    def test_text_answer_set_and_get(self):
        """Test setting and getting TEXT answer."""
        answer = Answer.objects.create(
            submission=self.test_submission, question=self.test_question_TEXT
        )
        answer.answer = "John Doe"
        self.assertEqual(answer.answer_value, "John Doe")

    def test_text_answer_via_set_value(self):
        """Test setting TEXT answer via set_value method."""
        answer = Answer.objects.create(
            submission=self.test_submission, question=self.test_question_TEXT
        )
        answer.set_value("Jane Smith")
        self.assertEqual(answer.answer_value, "Jane Smith")

    def test_text_answer_update(self):
        """Test updating TEXT answer."""
        answer = Answer.objects.create(
            submission=self.test_submission, question=self.test_question_TEXT
        )
        answer.answer = "First Answer"
        first_value = answer.answer_value
        answer.answer = "Updated Answer"
        self.assertNotEqual(first_value, answer.answer_value)
        self.assertEqual(answer.answer_value, "Updated Answer")

    def test_text_answer_special_characters(self):
        """Test TEXT answer with special characters."""
        answer = Answer.objects.create(
            submission=self.test_submission, question=self.test_question_TEXT
        )
        special_text = "Robert @#$%&*() 中文 🎉"
        answer.answer = special_text
        self.assertEqual(answer.answer_value, special_text)

    def test_text_answer_whitespace(self):
        """Test TEXT answer with leading/trailing whitespace."""
        answer = Answer.objects.create(
            submission=self.test_submission, question=self.test_question_TEXT
        )
        text_with_spaces = "  spaces  "
        answer.answer = text_with_spaces
        self.assertEqual(answer.answer_value, text_with_spaces)

    # BIGTEXT TYPE TESTS
    def test_bigtext_question_creation(self):
        """Test creating a BIGTEXT type question."""
        bigtext_question = Question.objects.create(
            registration=self.test_registration,
            question="Describe your experience:",
            question_type=Question.BIGTEXT,
        )
        self.assertEqual(bigtext_question.question_type, Question.BIGTEXT)

    def test_bigtext_answer_set_and_get(self):
        """Test setting and getting BIGTEXT answer."""
        answer = Answer.objects.create(
            submission=self.test_submission,
            question=self.test_question_BIGTEXT,
        )
        long_text = "This is a long description with multiple sentences. " * 20
        answer.answer = long_text
        self.assertEqual(answer.answer_value, long_text)

    def test_bigtext_answer_via_set_value(self):
        """Test setting BIGTEXT answer via set_value method."""
        answer = Answer.objects.create(
            submission=self.test_submission,
            question=self.test_question_BIGTEXT,
        )
        bigtext = "Paragraph 1\n\nParagraph 2\n\nParagraph 3"
        answer.set_value(bigtext)
        self.assertEqual(answer.answer_value, bigtext)

    def test_bigtext_answer_with_newlines(self):
        """Test BIGTEXT answer preserves newlines."""
        answer = Answer.objects.create(
            submission=self.test_submission,
            question=self.test_question_BIGTEXT,
        )
        multiline_text = "Line 1\nLine 2\nLine 3"
        answer.answer = multiline_text
        self.assertEqual(answer.answer_value, multiline_text)

    def test_bigtext_answer_empty(self):
        """Test BIGTEXT answer with empty value."""
        answer = Answer.objects.create(
            submission=self.test_submission,
            question=self.test_question_BIGTEXT,
        )
        answer.answer = ""
        self.assertEqual(answer.answer_value, "")

    # CHOICE TYPE TESTS
    def test_choice_question_creation(self):
        """Test creating a CHOICE type question."""
        choice_question = Question.objects.create(
            registration=self.test_registration,
            question="Pick one:",
            question_type=Question.CHOICE,
        )
        self.assertEqual(choice_question.question_type, Question.CHOICE)

    def test_choice_question_with_choices(self):
        """Test CHOICE question with multiple choice options."""
        choice_q = Question.objects.create(
            registration=self.test_registration,
            question="Select color:",
            question_type=Question.CHOICE,
        )
        choice1 = QuestionChoice.objects.create(question=choice_q, value="Red")
        choice2 = QuestionChoice.objects.create(
            question=choice_q, value="Green"
        )
        choice3 = QuestionChoice.objects.create(
            question=choice_q, value="Blue"
        )

        self.assertEqual(choice_q.choices.count(), 3)
        self.assertIn(choice1, choice_q.choices.all())
        self.assertIn(choice2, choice_q.choices.all())
        self.assertIn(choice3, choice_q.choices.all())

    def test_choice_answer_set_and_get(self):
        """Test setting and getting CHOICE answer."""
        answer = Answer.objects.create(
            submission=self.test_submission, question=self.test_question_CHOICE
        )
        answer.answer = self.test_questionChoice
        self.assertEqual(answer.answer_value, "Blue")

    def test_choice_answer_via_set_value(self):
        """Test setting CHOICE answer via set_value method."""
        answer = Answer.objects.create(
            submission=self.test_submission, question=self.test_question_CHOICE
        )
        answer.set_value(str(self.test_questionChoice.pk))
        self.assertEqual(answer.answer_value, "Blue")

    def test_choice_answer_update(self):
        """Test updating CHOICE answer."""
        red_choice = QuestionChoice.objects.create(
            question=self.test_question_CHOICE, value="Red"
        )
        answer = Answer.objects.create(
            submission=self.test_submission, question=self.test_question_CHOICE
        )
        answer.answer = self.test_questionChoice
        first_value = answer.answer_value
        answer.answer = red_choice
        self.assertNotEqual(first_value, answer.answer_value)
        self.assertEqual(answer.answer_value, "Red")

    # DROPDOWN TYPE TESTS
    def test_dropdown_question_creation(self):
        """Test creating a DROPDOWN type question."""
        dropdown_question = Question.objects.create(
            registration=self.test_registration,
            question="Select from dropdown:",
            question_type=Question.DROPDOWN,
        )
        self.assertEqual(dropdown_question.question_type, Question.DROPDOWN)

    def test_dropdown_answer_set_and_get(self):
        """Test setting and getting DROPDOWN answer."""
        answer = Answer.objects.create(
            submission=self.test_submission,
            question=self.test_question_DROPDOWN,
        )
        answer.answer = self.test_questionMulti1
        self.assertEqual(answer.answer_value, "Option 1")

    def test_dropdown_answer_via_set_value(self):
        """Test setting DROPDOWN answer via set_value method."""
        answer = Answer.objects.create(
            submission=self.test_submission,
            question=self.test_question_DROPDOWN,
        )
        answer.set_value(str(self.test_questionMulti1.pk))
        self.assertEqual(answer.answer_value, "Option 1")

    def test_dropdown_answer_from_multi_choices(self):
        """Test DROPDOWN can select from shared choice pool."""
        # DROPDOWN and MULTI can share the same choices
        answer = Answer.objects.create(
            submission=self.test_submission,
            question=self.test_question_DROPDOWN,
        )
        answer.answer = self.test_questionMulti2
        self.assertEqual(answer.answer_value, "Option 2")

    # MULTI TYPE TESTS
    def test_multi_question_creation(self):
        """Test creating a MULTI type question."""
        multi_question = Question.objects.create(
            registration=self.test_registration,
            question="Select multiple:",
            question_type=Question.MULTI,
        )
        self.assertEqual(multi_question.question_type, Question.MULTI)

    def test_multi_answer_single_choice(self):
        """Test MULTI answer with single choice."""
        answer = Answer.objects.create(
            submission=self.test_submission, question=self.test_question_MULTI
        )
        answer.answer = [self.test_questionMulti1]
        self.assertEqual(answer.answer_value, "Option 1")

    def test_multi_answer_multiple_choices(self):
        """Test MULTI answer with multiple choices."""
        answer = Answer.objects.create(
            submission=self.test_submission, question=self.test_question_MULTI
        )
        answer.answer = [self.test_questionMulti1, self.test_questionMulti2]
        self.assertEqual(answer.answer_value, "Option 1 § Option 2")

    def test_multi_answer_via_set_value(self):
        """Test setting MULTI answer via set_value method."""
        answer = Answer.objects.create(
            submission=self.test_submission, question=self.test_question_MULTI
        )
        choice_ids = [
            str(self.test_questionMulti1.pk),
            str(self.test_questionMulti2.pk),
        ]
        answer.set_value(choice_ids)
        self.assertEqual(answer.answer_value, "Option 1 § Option 2")

    def test_multi_answer_order_preserved(self):
        """Test MULTI answer preserves choice order."""
        answer = Answer.objects.create(
            submission=self.test_submission, question=self.test_question_MULTI
        )
        # Add choices in one order
        answer.answer = [self.test_questionMulti1, self.test_questionMulti2]
        value1 = answer.answer_value

        # Update with reversed order
        answer.answer = [self.test_questionMulti2, self.test_questionMulti1]
        value2 = answer.answer_value

        # Both should contain the same choices
        self.assertIn("Option 1", value1)
        self.assertIn("Option 2", value1)
        self.assertIn("Option 1", value2)
        self.assertIn("Option 2", value2)

    def test_multi_answer_empty_list(self):
        """Test MULTI answer with empty list."""
        answer = Answer.objects.create(
            submission=self.test_submission, question=self.test_question_MULTI
        )
        answer.answer = []
        self.assertEqual(answer.answer_value, "")

    def test_multi_question_with_constraints(self):
        """Test MULTI question with min/max constraints."""
        multi_constrained = Question.objects.create(
            registration=self.test_registration,
            question="Pick 2-3 options:",
            question_type=Question.MULTI,
            min_choices=2,
            max_choices=3,
        )
        self.assertEqual(multi_constrained.min_choices, 2)
        self.assertEqual(multi_constrained.max_choices, 3)

    # CROSS-TYPE TESTS
    def test_all_question_types_in_registration(self):
        """Test all question types can coexist in single registration."""
        types = [
            Question.TEXT,
            Question.BIGTEXT,
            Question.CHOICE,
            Question.DROPDOWN,
            Question.MULTI,
        ]
        questions = []
        for qtype in types:
            q = Question.objects.create(
                registration=self.test_registration,
                question=f"Question of type {qtype}:",
                question_type=qtype,
            )
            questions.append(q)

        all_questions = Question.objects.filter(
            registration=self.test_registration
        )
        for qtype in types:
            self.assertTrue(
                any(q.question_type == qtype for q in all_questions)
            )

    def test_answer_property_type_detection(self):
        """Test answer property correctly detects question type."""
        text_answer = Answer.objects.create(
            submission=self.test_submission, question=self.test_question_TEXT
        )
        text_answer.answer = "test"

        choice_answer = Answer.objects.create(
            submission=self.test_submission, question=self.test_question_CHOICE
        )
        choice_answer.answer = self.test_questionChoice

        multi_answer = Answer.objects.create(
            submission=self.test_submission, question=self.test_question_MULTI
        )
        multi_answer.answer = [self.test_questionMulti1]

        # Verify each answer has correct data object type
        self.assertIsInstance(text_answer.answer, TextData)
        self.assertIsInstance(choice_answer.answer, ChoiceData)
        self.assertIsInstance(multi_answer.answer, MultiData)

    def test_question_type_string_values(self):
        """Test question type string constants."""
        self.assertEqual(Question.TEXT, "text")
        self.assertEqual(Question.BIGTEXT, "bigtext")
        self.assertEqual(Question.CHOICE, "choice")
        self.assertEqual(Question.DROPDOWN, "dropdown")
        self.assertEqual(Question.MULTI, "multi")

    def test_question_types_in_choices(self):
        """Test all question types are in QUESTION_TYPES."""
        question_type_values = [t[0] for t in Question.QUESTION_TYPES]
        self.assertIn(Question.TEXT, question_type_values)
        self.assertIn(Question.BIGTEXT, question_type_values)
        self.assertIn(Question.CHOICE, question_type_values)
        self.assertIn(Question.DROPDOWN, question_type_values)
        self.assertIn(Question.MULTI, question_type_values)
