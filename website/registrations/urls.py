from django.urls import path

from registrations.views import Step2View, Step1View

app_name = 'registrations'
urlpatterns = [
    path('', Step1View.as_view()),
    path('step1', Step1View.as_view(), name='step1'),
    path('step2', Step2View.as_view(), name='step2')
]
