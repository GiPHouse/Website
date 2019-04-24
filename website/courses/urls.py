from courses.views import CoursesView

from django.urls import path

app_name = 'courses'
urlpatterns = [
    path('<int:year>/<slug:season>/', CoursesView.as_view(), name='lectures'),
]
