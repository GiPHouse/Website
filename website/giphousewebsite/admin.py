from django.contrib import admin
from django.contrib.auth.models import Group

admin.site.site_header = "Giphouse Administration"
admin.site.site_title = "Giphouse"

admin.site.unregister(Group)
