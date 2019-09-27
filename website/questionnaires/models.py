from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

from courses.models import Semester

from registrations.models import Employee

User: Employee = get_user_model()


class QuestionnaireManager(models.Manager):
    """Manager for the Questionnaire model."""

    def current_questionnaires(self):
        """Get all questionnaires of the current semester."""
        return self.filter(semester=Semester.objects.get_current_semester())


class Questionnaire(models.Model):
    """A group of questions."""

    class Meta:
        """Meta class describing the order of the Questionnaire model."""

        ordering = ["-available_until_hard", "-available_until_soft", "-available_from"]

    title = models.CharField(max_length=200)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    available_from = models.DateTimeField(
        default=timezone.now, help_text="The moment from which the questionnaire is available."
    )
    available_until_soft = models.DateTimeField(
        help_text="Soft deadline to submit the questionnaire, after this the submission is marked as late."
    )
    available_until_hard = models.DateTimeField(
        help_text="Hard deadline to submit the questionnaire. No submissions possible after this date."
    )

    objects = QuestionnaireManager()

    @property
    def is_open(self):
        """Return True if neither the deadline nor the late deadline have passed."""
        return (
            self.available_from <= timezone.now() <= self.available_until_soft
            and self.available_until_hard >= timezone.now()
        )

    @property
    def is_late(self):
        """Return True if the deadline but not the late deadline has passed."""
        return (
            self.available_from < timezone.now() <= self.available_until_hard
            and self.available_until_soft < timezone.now()
        )

    @property
    def is_closed(self):
        """Return True if the deadline and the late deadline have passed."""
        return (
            self.available_from < timezone.now()
            and self.available_until_soft < timezone.now()
            and self.available_until_hard < timezone.now()
        )

    def get_until_date(self):
        """Return the date that the questionnaire closes."""
        if self.is_open:
            return self.available_until_soft

        elif self.is_late:
            return self.available_until_hard

        return None

    def __str__(self):
        """Return title."""
        return f"{self.title} ({self.semester})"


class QuestionnaireSubmission(models.Model):
    """Submission of a questionnaire by a user."""

    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE)
    participant = models.ForeignKey(Employee, on_delete=models.CASCADE)

    late = models.BooleanField()
    created = models.DateTimeField(auto_now_add=True)

    def save(self, **kwargs):
        """Save model and set on_time field."""
        self.late = timezone.now() > self.questionnaire.available_until_soft
        super().save(**kwargs)

    def __str__(self):
        """Return string representation of the submission."""
        return self.questionnaire.title


class Question(models.Model):
    """Question model."""

    OPEN = 0
    QUALITY = 1
    AGREEMENT = 2

    CHOICES = (
        (OPEN, "Open question"),
        (QUALITY, "Poor/good Likert scale"),
        (AGREEMENT, "Disagree/agree Likert scale"),
    )

    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE)
    question = models.CharField(max_length=200)
    question_type = models.PositiveSmallIntegerField(choices=CHOICES)
    about_team_member = models.BooleanField(default=False)

    @property
    def is_closed(self):
        """Return True if the question is closed."""
        return self.question_type != self.OPEN

    def get_likert_choices(self):
        """Get the appropriate choices for the question."""
        if self.question_type == self.QUALITY:
            return QualityAnswerData.CHOICES

        elif self.question_type == self.AGREEMENT:
            return AgreementAnswerData.CHOICES

        return ()

    def __str__(self):
        """Return question string."""
        return self.question


class Answer(models.Model):
    """Answer to a question."""

    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    submission = models.ForeignKey(QuestionnaireSubmission, on_delete=models.CASCADE)

    peer = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="+", blank=True, null=True)

    @property
    def answer(self):
        """Get the correct answer value."""
        if self.question.question_type == Question.OPEN:
            try:
                return self.openanswerdata
            except OpenAnswerData.DoesNotExist:
                return None

        elif self.question.question_type == Question.AGREEMENT:
            try:
                return self.agreementanswerdata
            except AgreementAnswerData.DoesNotExist:
                return None

        else:
            try:
                return self.qualityanswerdata
            except QualityAnswerData.DoesNotExist:
                return None

    @answer.setter
    def answer(self, value):
        """Set the correct answer value."""
        if self.question.question_type == Question.OPEN:
            try:
                self.openanswerdata.value = value
            except OpenAnswerData.DoesNotExist:
                self.openanswerdata = OpenAnswerData(answer=self, value=value)
            self.openanswerdata.save()

        elif self.question.question_type == Question.AGREEMENT:
            try:
                self.agreementanswerdata.value = value
            except AgreementAnswerData.DoesNotExist:
                self.agreementanswerdata = AgreementAnswerData(answer=self, value=value)
            self.agreementanswerdata.save()

        else:
            try:
                self.qualityanswerdata.value = value
            except QualityAnswerData.DoesNotExist:
                self.qualityanswerdata = QualityAnswerData(answer=self, value=value)
            self.qualityanswerdata.save()

    def __str__(self):
        """Return string representation of the answer."""
        return f"{self.submission.participant} answers #{self.question.id}"


class OpenAnswerData(models.Model):
    """Model storing value of an open question."""

    answer = models.OneToOneField(Answer, on_delete=models.CASCADE)
    value = models.TextField()

    def __str__(self):
        """Return value."""
        return self.value


class AbstractLikertData(models.Model):
    """Abstract class describing Likert answer."""

    answer = models.OneToOneField(Answer, on_delete=models.CASCADE, related_name="%(class)s")

    class Meta:
        """Meta class making sure this model is abstract."""

        abstract = True

    def __str__(self):
        """Return string representation of the value."""
        value = self.get_value_display()
        return f"{value} ({self.value})" if value is not None else ""


class AgreementAnswerData(AbstractLikertData):
    """Model representing a Likert value describing agreement."""

    STRONGLY_DISAGREE = 1
    DISAGREE = 2
    NEUTRAL = 3
    AGREE = 4
    STRONGLY_AGREE = 5

    CHOICES = (
        (STRONGLY_DISAGREE, "Strongly Disagree"),
        (DISAGREE, "Disagree"),
        (NEUTRAL, "Neutral"),
        (AGREE, "Agree"),
        (STRONGLY_AGREE, "Strongly Agree"),
    )

    value = models.PositiveSmallIntegerField(choices=CHOICES)


class QualityAnswerData(AbstractLikertData):
    """Model representing a Likert value describing quality."""

    VERY_POOR = 1
    POOR = 2
    AVERAGE = 3
    GOOD = 4
    VERY_GOOD = 5

    CHOICES = (
        (VERY_POOR, "Very Poor"),
        (POOR, "Poor"),
        (AVERAGE, "Average"),
        (GOOD, "Good"),
        (VERY_GOOD, "Very Good"),
    )

    value = models.PositiveSmallIntegerField(choices=CHOICES)
