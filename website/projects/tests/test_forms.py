from django.forms import modelform_factory
from django.test import TestCase

from projects.forms import (
    NewRepositoryInlineForm,
    ExistingRepositoryInlineForm,
)
from projects.models import Repository, NewRepository, ExistingRepository


class NewRepositoryInlineFormTest(TestCase):
    """
    Tests for __init__ logic of NewRepositoryInlineForm.
    Skips queryset filtering, instantiates the form itself.
    """

    @classmethod
    def setUpTestData(cls):
        cls.NewRepoForm = modelform_factory(
            model=NewRepository,
            form=NewRepositoryInlineForm,
            fields="__all__",
        )

    def test_init(self):
        form = self.NewRepoForm()

        self.assertEqual(
            form.fields["is_archived"].choices,
            Repository.Archived.choices[:-1],
        )

        self.assertIn(
            "Setting this to 'To be archived'",
            form.fields["is_archived"].help_text,
        )


class ExistingRepositoryInlineFormTest(TestCase):
    """
    Tests for __init__ logic of ExistingRepositoryInlineForm.
    Skips queryset filtering, instantiates the form itself.
    """

    @classmethod
    def setUpTestData(cls):
        cls.ExistingRepoForm = modelform_factory(
            model=ExistingRepository,
            form=ExistingRepositoryInlineForm,
            fields="__all__",
        )

    def test_new_obj(self):
        form = self.ExistingRepoForm()

        self.assertIn(
            "Pasting the repository id",
            form.fields["github_repo_id"].help_text,
        )

        self.assertEqual(
            form.fields["github_repo_id"].widget.attrs["class"],
            "github_repo_id-field",
        )

    def test_existing_obj_confirmed_archived_repo(self):
        repo = ExistingRepository.objects.create(
            name="charles",
            is_archived=Repository.Archived.CONFIRMED,
        )

        form = self.ExistingRepoForm(instance=repo)

        self.assertTrue(form.fields["is_archived"].disabled)

        self.assertIn(
            "This repository is already archived on GitHub",
            form.fields["is_archived"].help_text,
        )

    def test_existing_obj(self):
        repo = ExistingRepository.objects.create(
            name="george",
            is_archived=Repository.Archived.NOT_ARCHIVED,
        )

        form = self.ExistingRepoForm(instance=repo)

        self.assertFalse(form.fields["is_archived"].disabled)

        self.assertEqual(
            form.fields["is_archived"].choices,
            Repository.Archived.choices[:-1],
        )

        self.assertIn(
            "Setting this to 'To be archived'",
            form.fields["is_archived"].help_text,
        )

        self.assertTrue(form.fields["github_repo_id"].disabled)

        self.assertIn(
            "This is the id",
            form.fields["github_repo_id"].help_text,
        )
