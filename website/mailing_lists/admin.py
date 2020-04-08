from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path

from mailing_lists.gsuite import GSuiteSyncService
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

    list_display = ("address", "description")
    list_filter = ("address",)
    inlines = [ExtraEmailInline, AliasInline]
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
        sync.sync_mailing_lists()
        return redirect("/admin/mailing_lists/mailinglist")

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
