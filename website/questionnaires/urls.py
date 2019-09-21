from django.urls import path

from questionnaires.views import OverviewView, QuestionnaireView

app_name = "questionnaires"

urlpatterns = [
    path("", OverviewView.as_view(), name="overview"),
    path("<int:questionnaire>", QuestionnaireView.as_view(), name="questionnaire"),
]
