from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models

from projects.models import Project

from registrations.models import Employee


email_local_part_validator = RegexValidator(
    regex=r"^[a-zA-Z0-9-]+$", message="Enter a simpler name"
)  # TODO test this validator

reserved_addresses_validator = RegexValidator(
    regex=r"^(?!(abuse|admin|administrator|hostmaster|majordomo|postmaster|root|ssl-admin|webmaster)$)",
    message="This is a reserved address",
)


class MailingList(models.Model):
    """Mailing list with recipients."""

    address = models.CharField(
        max_length=60, validators=[email_local_part_validator, reserved_addresses_validator], unique=True
    )
    description = models.CharField(blank=True, max_length=100)
    projects = models.ManyToManyField(Project, blank=True)
    users = models.ManyToManyField(Employee, blank=True)

    def validate_unique(self, exclude=None):
        """Validate uniqueness of the mailing list email address."""
        if len(MailingListAlias.objects.filter(address=self.address)):
            raise ValidationError("This email address is already in use as an alias.")
        super(MailingList, self).validate_unique(exclude)

    def save(self, *args, **kwargs):
        """Save the model if it is valid."""
        self.validate_unique()
        super(MailingList, self).save(*args, **kwargs)

    def __str__(self):
        """Return mailing list address and name."""
        return f"Mailing list {self.address}"

    @property
    def email_address(self):
        """Return the full email address associated with this mailing list."""
        return self.address + "@" + settings.GSUITE_DOMAIN

    @property
    def all_addresses(self):
        """Return all email addresses that are in the mailing list."""
        project_emails = []
        for project in self.projects.all():
            for employee in project.get_employees():
                project_emails.append(employee.email)

        user_emails = []
        for user in self.users.all():
            user_emails.append(user.email)

        extra_emails = []
        for extra in self.extraemailaddress_set.all():
            extra_emails.append(extra.address)

        return set(project_emails + user_emails + extra_emails)


class ExtraEmailAddress(models.Model):
    """Bare email address with no associated user."""

    class Meta:
        """Meta class for ExtraEmailAddress model."""

        verbose_name_plural = "Extra Email Addresses"

    address = models.EmailField(blank=False)
    name = models.CharField(blank=False, max_length=50)
    mailing_list = models.ForeignKey(MailingList, on_delete=models.CASCADE)

    def __str__(self):
        """Return mailing address and name."""
        return f"{self.address} ({self.name})"


class MailingListAlias(models.Model):
    """An alias for a mailing list."""

    class Meta:
        """Meta class for MailingListAlias model."""

        verbose_name_plural = "mailing list aliases"

    address = models.CharField(
        max_length=60, validators=[email_local_part_validator, reserved_addresses_validator], unique=True
    )
    mailing_list = models.ForeignKey(MailingList, on_delete=models.CASCADE)

    def validate_unique(self, exclude=None):
        """Validate uniqueness of mailing list alias email address."""
        if self.mailing_list.address == self.address:
            raise ValidationError("Alias address cannot be the same as the mailing list address.")
        if len(MailingList.objects.filter(address=self.address)):
            raise ValidationError("Email address is already in use as a mailing list.")
        super(MailingListAlias, self).validate_unique(exclude)

    def save(self, *args, **kwargs):
        """Save the model if it is valid."""
        self.validate_unique()
        super(MailingListAlias, self).save(*args, **kwargs)

    @property
    def email_address(self):
        """Return the full email address associated with this alias."""
        return self.address + "@" + settings.GSUITE_DOMAIN

    def __str__(self):
        """Return mailing alias address."""
        return f"{self.address}"
