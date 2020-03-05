import re

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models

from projects.models import Project

from registrations.models import Employee


domain_validator = RegexValidator(
    regex=f"@{re.escape(settings.GSUITE_DOMAIN)}$", message=f"Email address must end in @{settings.GSUITE_DOMAIN}",
)


class MailingList(models.Model):
    """Mailing list with recipients."""

    address = models.EmailField(blank=False, unique=True, validators=[domain_validator])
    name = models.CharField(blank=False, unique=True, max_length=50)
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
        return f"{self.address} ({self.name})"


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

    address = models.EmailField(blank=False, unique=True, validators=[domain_validator])
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

    def __str__(self):
        """Return mailing alias address."""
        return f"{self.address}"
