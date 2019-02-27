from django.http import HttpResponse
from django.shortcuts import render, get_list_or_404
from registrations.models import Project, Semester


def projectsview(request, year, semester):
    # projects variable is assigned a list of projects given by the year and semester parameters or returns a 404.
    projects = get_list_or_404(Project.objects.filter(semester__year=year).filter(semester__semester=semester))
    return render(request, "projects.html", context={'projects': projects})


def baseview(request):
    semesters = Semester.objects.all()
    return render(request, "base.html", context={'semesters': semesters})


def headerview(request):
    semesters = Semester.objects.all()

    return render(request, "header.html", context={'semesters': semesters})
