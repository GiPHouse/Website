from django.contrib import admin

from mailing_lists.models import (
    ExtraEmailAddress,
    MailingList,
    MailingListAlias,
)


class ExtraEmailInline(admin.TabularInline):
    """Inline for extra email addresses in mailing list."""

    model = ExtraEmailAddress
    extra = 0


class AliasInline(admin.TabularInline):
    """Inline for aliases of mailing list."""

    model = MailingListAlias
    extra = 0


@admin.register(MailingList)
class MailingListAdmin(admin.ModelAdmin):
    """Admin class for Mailing List."""

    list_display = ("address", "name")
    list_filter = ("address", "name")
    inlines = [ExtraEmailInline, AliasInline]
