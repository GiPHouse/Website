"""Module containing the url definition of the loefsys web app."""

from debug_toolbar.toolbar import debug_toolbar_urls
from django.contrib import admin
from django.urls import path

urlpatterns = [path("admin/", admin.site.urls), *debug_toolbar_urls()]
