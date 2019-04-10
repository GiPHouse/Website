from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, User as DjangoUser

User: DjangoUser = get_user_model()

admin.site.site_header = 'Giphouse Administration'
admin.site.site_title = 'Giphouse'

admin.site.unregister(DjangoUser)
admin.site.unregister(Group)
