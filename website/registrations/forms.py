import re
import logging

from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from registrations.models import Employee, registration

student_number_regex = re.compile(r"^[sS]?(\d{7})$")
wrong_email_regex = re.compile(r"^[sS]?(\d{7})@(?:student\.)?ru\.nl$")

User: Employee = get_user_model()
logger = logging.getLogger(__name__)


class Step2Form(forms.Form):
    """Form to get user information for registration."""

    ignore_warnings = forms.BooleanField(
        label="I acknowledge the warning(s) and want to proceed with the registration",
        required=False,
        initial=False,
    )

    def get_field_name(self, question, dynamic_user_fields):
        """ "Set field names for dynamic questions based on their label"""
        base = f"question_{question.id}"
        if question.label in dynamic_user_fields:
            return f"{base}_{question.label}"

        return base

    def get_user_field(self, label):
        return self.cleaned_data[self.user_fields[label]]

    class Media:
        js = ("js/question_type_toggle_step2.js",)

    def __init__(self, *args, session=None, **kwargs):
        super().__init__(*args, **kwargs)

        if session is None or "github_id" not in session:
            raise ValueError("GitHub session info is required for this form")

        github_id = session["github_id"]
        github_username = session["github_username"]
        dynamic_user_fields = {
            "first_name",
            "last_name",
            "email",
            "student_number",
            "course",
        }

        if github_id is None or github_username is None:
            raise ValueError("GitHub session info is incomplete")

        self.github_id = github_id
        self.github_username = github_username
        self.user_fields = {}
        self.warnings = []
        self.dynamic_questions = []
        self.questions_by_id = {}

        current_registration = (
            registration.Registrations.objects.current_registration()
        )

        if not current_registration:
            raise ValueError("No registration found for the current semester")

        logger.warning(
            "Step2 loaded registration %s with %s questions",
            current_registration.title,
            current_registration.question_set.count(),
        )

        all_questions = list(
            current_registration.question_set.select_related(
                "parent_choice__question"
            ).prefetch_related("choices")
        )

        self.dynamic_questions = all_questions
        self.questions_by_id = {q.id: q for q in all_questions}
        root_questions = [
            q for q in all_questions if q.parent_choice_id is None
        ]

        logger.warning(
            "Dynamic questions: %s",
            [(q.id, q.question) for q in all_questions],
        )
        logger.warning(
            "Questions by ID: %s", {q.id: q.question for q in all_questions}
        )
        logger.warning(
            "Root questions: %s", [(q.id, q.question) for q in root_questions]
        )

        self.ordered_question_list = self.ordered_questions()
        source_data = self.data if self.is_bound else self.initial
        self.active_questions_ids_list = self._get_active_question_ids(
            source_data
        )

        for q in self.ordered_question_list:
            logger.warning(
                (
                    "Question debug: id=%s registration_id=%s "
                    "parent_choice_id=%s  parent_choice=%s type=%s optional=%s "
                    "min_choices=%s max_choices=%s warnings=%s text=%r "
                    "choices=%s"
                ),
                q.id,
                q.registration_id,
                q.parent_choice_id,
                q.parent_choice.question.id
                if q.parent_choice and q.parent_choice.question
                else None,
                q.question_type,
                q.optional,
                q.min_choices,
                q.max_choices,
                q.warnings,
                q.question,
                list(q.choices.values_list("id", "value", "follow_up")),
            )

            field_name = self.get_field_name(q, dynamic_user_fields)
            if q.label in dynamic_user_fields:
                self.user_fields[q.label] = field_name

            is_follow_up = q.parent_choice_id is not None
            widget_attrs = {
                "question-id": str(q.id),
                "text": q.question,
            }
            if is_follow_up:
                widget_attrs["parent-choice-id"] = str(q.parent_choice_id)
                widget_attrs["parent-question-id"] = str(
                    q.parent_choice.question_id
                )
                widget_attrs["follow-up-required"] = (
                    "1" if not q.optional else "0"
                )

            if q.question_type == registration.Question.TEXT:
                self.fields[field_name] = forms.CharField(
                    label=q.question,
                    required=False if is_follow_up else not q.optional,
                    widget=forms.TextInput(attrs=widget_attrs),
                )

            elif q.question_type == registration.Question.CHOICE:
                choices = registration.QuestionChoice.objects.filter(
                    question=q
                ).values_list("id", "value")
                self.fields[field_name] = forms.ChoiceField(
                    label=q.question,
                    choices=choices,
                    required=False if is_follow_up else not q.optional,
                    widget=forms.RadioSelect(attrs=widget_attrs),
                )

            elif q.question_type == registration.Question.MULTI:
                choices = registration.QuestionChoice.objects.filter(
                    question=q
                ).values_list("id", "value")
                self.fields[field_name] = forms.MultipleChoiceField(
                    label=q.question,
                    choices=choices,
                    required=not q.optional,
                    widget=forms.CheckboxSelectMultiple,
                )

            elif q.question_type == registration.Question.BIGTEXT:
                self.fields[field_name] = forms.CharField(
                    label=q.question,
                    required=not q.optional,
                    widget=forms.Textarea,
                )

            elif q.question_type == registration.Question.DROPDOWN:
                choices = [("", "-- Select an option --")] + list(
                    registration.QuestionChoice.objects.filter(
                        question=q
                    ).values_list("id", "value")
                )
                self.fields[field_name] = forms.ChoiceField(
                    label=q.question,
                    choices=choices,
                    required=not q.optional,
                    widget=forms.Select,
                )

            elif q.question_type == registration.Question.TEXTLIST:
                n_fields = q.max_choices if q.max_choices is not None else 1
                for i in range(n_fields):
                    self.fields[f"{field_name}_{i}"] = forms.CharField(
                        label=f"{q.question} {i + 1}",
                        required=False,
                        widget=forms.TextInput(attrs=widget_attrs),
                    )

            elif q.question_type == registration.Question.CHOICELIST:
                choices = [("", "-- Select a project --")] + [
                    (p.id, p.name) for p in current_registration.get_projects()
                ]
                n_fields = q.max_choices if q.max_choices is not None else 1
                for i in range(n_fields):
                    self.fields[f"{field_name}_{i}"] = forms.ChoiceField(
                        label=f"{q.question} {i + 1}",
                        choices=choices,
                        required=False,
                        widget=forms.Select(attrs=widget_attrs),
                    )

            else:
                raise ValueError(f"Unknown question type: {q.question_type}")

        if not self.is_bound:
            github_name = session.get("github_name", "") or ""
            github_email = session.get("github_email", "") or ""
            try:
                first_name, last_name = github_name.rsplit(" ", 1)
            except ValueError:
                first_name, last_name = github_name, ""

            initial_values = {
                "first_name": first_name,
                "last_name": last_name,
                "email": github_email,
            }

            for label, value in initial_values.items():
                field_name = self.user_fields.get(label)
                if field_name and field_name in self.fields:
                    self.fields[field_name].initial = value

        ignore_warnings_field = self.fields.pop("ignore_warnings", None)
        if ignore_warnings_field is not None:
            self.fields["ignore_warnings"] = ignore_warnings_field

    def ordered_questions(self):
        ordered = []
        added_ids = set()

        follow_ups_by_parent_choice = {}
        for q in self.dynamic_questions:
            if q.parent_choice_id is not None:
                if q.parent_choice_id not in follow_ups_by_parent_choice:
                    follow_ups_by_parent_choice[q.parent_choice_id] = []
                follow_ups_by_parent_choice[q.parent_choice_id].append(q)

        logger.warning(
            "Follow-ups by parent: %s",
            {
                parent_id: [(q.id, q.question) for q in follow_ups]
                for parent_id, follow_ups in follow_ups_by_parent_choice.items()
            },
        )

        def add_question_and_follow_ups(q):
            if q.id in added_ids:
                return
            ordered.append(q)
            added_ids.add(q.id)
            for choice in q.choices.all():
                follow_ups = follow_ups_by_parent_choice.get(choice.id, [])
                for follow_up in follow_ups:
                    add_question_and_follow_ups(follow_up)

        for q in self.dynamic_questions:
            if q.parent_choice_id is None:
                add_question_and_follow_ups(q)

        logger.warning(
            "Ordered questions: %s", [(q.id, q.question) for q in ordered]
        )

        return ordered

    def _get_active_question_ids(self, data):
        active_ids = set()

        for q in self.ordered_question_list:
            if q.parent_choice_id is None:
                active_ids.add(q.id)
            else:
                parent_field = f"question_{q.parent_choice.question_id}"
                parent_value = data.get(parent_field)

                if parent_value is not None:
                    if str(q.parent_choice_id) == str(parent_value):
                        active_ids.add(q.id)

        return active_ids

    def check_subfield_list(self, question_id, question, cleaned_data):
        """Shared validation for CHOICELIST and TEXTLIST subfield questions."""
        n_fields = (
            question.max_choices if question.max_choices is not None else 1
        )
        values = []
        for i in range(n_fields):
            subfield = f"question_{question_id}_{i}"
            val = cleaned_data.get(subfield, "")
            if val:
                values.append((subfield, val))

        if (
            question.min_choices is not None
            and len(values) < question.min_choices
        ):
            self.warnings.append(
                (
                    f"question_{question_id}_0",
                    f"At least {question.min_choices} values are required.",
                )
            )

        all_subfields = [
            f"question_{question_id}_{j}" for j in range(n_fields)
        ]
        for j, (subfield, val) in enumerate(values):
            cleaned_data[all_subfields[j]] = val
        for j in range(len(values), n_fields):
            cleaned_data[all_subfields[j]] = ""

        if len(values) >= 2:
            seen = set()
            for subfield, val in values:
                if val in seen:
                    self.warnings.append(
                        (subfield, "You cannot enter the same value twice.")
                    )
                seen.add(val)

        if question.warnings:
            self.warnings.append(
                (f"question_{question_id}_0", question.warnings.strip())
            )

        return values

    def clean(self):
        cleaned_data = super().clean()
        active_ids = self._get_active_question_ids(cleaned_data)
        checked_subfield_questions = set()

        email_field = self.user_fields.get("email")
        if email_field:
            email = cleaned_data.get(email_field)
            if email:
                if (
                    User.objects.exclude(github_id=self.github_id)
                    .filter(email=email)
                    .exists()
                ):
                    self.add_error(
                        email_field,
                        ValidationError(
                            "Email address already in use.", code="exists"
                        ),
                    )
                elif wrong_email_regex.match(email) is not None:
                    self.add_error(
                        email_field,
                        ValidationError(
                            "Non-existent email address.", code="invalid"
                        ),
                    )

        student_number_field = self.user_fields.get("student_number")
        if student_number_field:
            student_number = cleaned_data.get(student_number_field)
            if student_number:
                m = student_number_regex.match(student_number)
                if m is None:
                    self.add_error(
                        student_number_field,
                        ValidationError(
                            "Invalid Student Number", code="invalid"
                        ),
                    )
                else:
                    student_number = "s" + m.group(1)
                    cleaned_data[student_number_field] = student_number
                    if (
                        User.objects.exclude(github_id=self.github_id)
                        .filter(student_number=student_number)
                        .exists()
                    ):
                        self.add_error(
                            student_number_field,
                            ValidationError(
                                "Student Number already in use.", code="exists"
                            ),
                        )

        for field_name in list(self.fields):
            if field_name.startswith("question_"):
                parts = field_name.split("_")
                question_id = int(parts[1])

                if question_id not in active_ids:
                    cleaned_data.pop(field_name, None)
                else:
                    question = self.questions_by_id.get(question_id)
                    if question is not None:
                        answer = cleaned_data.get(field_name)
                        is_follow_up = question.parent_choice_id is not None

                        if (
                            is_follow_up
                            and not question.optional
                            and not answer
                        ):
                            self.warnings.append(
                                (field_name, "This field is required.")
                            )

                        elif (
                            question.question_type
                            == registration.Question.DROPDOWN
                            and not question.optional
                            and not answer
                        ):
                            self.warnings.append(
                                (field_name, "Please select an option.")
                            )

                        elif (
                            question.question_type
                            == registration.Question.MULTI
                            and answer
                        ):
                            selected_count = len(answer)

                            if (
                                question.min_choices is not None
                                and selected_count < question.min_choices
                            ):
                                self.warnings.append(
                                    (
                                        field_name,
                                        f"At least {question.min_choices} choices are required (you selected {selected_count}).",
                                    )
                                )

                            if (
                                question.max_choices is not None
                                and selected_count > question.max_choices
                            ):
                                self.warnings.append(
                                    (
                                        field_name,
                                        f"No more than {question.max_choices} choices are allowed (you selected {selected_count}).",
                                    )
                                )

                            if question.warnings:
                                self.warnings.append(
                                    (field_name, question.warnings.strip())
                                )

                        elif (
                            question.question_type
                            in [
                                registration.Question.CHOICELIST,
                                registration.Question.TEXTLIST,
                            ]
                            and question.id not in checked_subfield_questions
                        ):
                            checked_subfield_questions.add(question.id)
                            self.check_subfield_list(
                                question_id, question, cleaned_data
                            )

        if self.warnings and not self.cleaned_data.get("ignore_warnings"):
            for field_name, message in self.warnings:
                self.add_error(field_name, message)

        return cleaned_data
