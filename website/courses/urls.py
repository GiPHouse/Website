from django.urls import path

from courses.views import CoursesView

app_name = 'courses'
urlpatterns = [
    path('<int:year>/<str:season>/', CoursesView.as_view(), name='lectures'),
]
