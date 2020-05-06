from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path

from mailing_lists.forms import AddressSuffixedForm
from mailing_lists.gsuite import GSuiteSyncService
from mailing_lists.models import (
    ExtraEmailAddress,
    MailingList,
    MailingListAlias,
    MailingListCourseSemesterLink,
)


class ExtraEmailInline(admin.TabularInline):
    """Inline for extra email addresses in mailing list."""

    model = ExtraEmailAddress
    extra = 0


class AliasInline(admin.TabularInline):
    """Inline for aliases of mailing list."""

    model = MailingListAlias
    extra = 0
    form = AddressSuffixedForm


class CourseSemesterLinkInline(admin.TabularInline):
    """Inline for the link to Course and Semester."""

    model = MailingListCourseSemesterLink
    extra = 1

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        """Change widgets for course and semester to remove add and change buttons."""
        formfield = super(CourseSemesterLinkInline, self).formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name in ["course", "semester"]:
            formfield.widget.can_add_related = False
            formfield.widget.can_change_related = False
        return formfield


@admin.register(MailingList)
class MailingListAdmin(admin.ModelAdmin):
    """Admin class for Mailing List."""

    form = AddressSuffixedForm
    list_display = ("address", "description")
    list_filter = ("address",)
    inlines = [CourseSemesterLinkInline, ExtraEmailInline, AliasInline]
    actions = ["synchronize_selected_mailing_lists"]

    def synchronize_selected_mailing_lists(self, request, queryset):
        """Synchronize all selected mailing lists with Gsuite."""
        sync = GSuiteSyncService()

        sync_list = []
        for list in queryset:
            sync_list.append(sync.mailing_list_to_group(list))

        sync.sync_mailing_lists(sync_list)

    synchronize_selected_mailing_lists.short_description = "Synchronize selected mailing lists"

    def synchronize_all_mailing_lists(self, request):
        """Synchronize all mailing lists with Gsuite, including automatic lists."""
        sync = GSuiteSyncService()
        task_id = sync.sync_mailing_lists_as_task()
        return redirect("admin:progress_bar", task=task_id)

    def get_urls(self):
        """Get admin urls."""
        urls = super().get_urls()
        custom_urls = [
            path(
                "sync-to-gsuite/",
                self.admin_site.admin_view(self.synchronize_all_mailing_lists),
                name="synchronize_to_gsuite",
            ),
        ]
        return custom_urls + urls
