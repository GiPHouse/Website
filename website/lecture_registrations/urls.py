from django.urls import path

from lecture_registrations.views import LectureRegistrationView
from lecture_registrations.views import LectureUnregistrationView

app_name = "lecture_registrations"

urlpatterns = [
    path("<int:pk>/register", LectureRegistrationView.as_view(), name="register_for_lecture"),
    path("<int:pk>/unregister", LectureUnregistrationView.as_view(), name="unregister_for_lecture"),
]
