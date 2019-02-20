from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.db import transaction, IntegrityError
from django.shortcuts import redirect
from django.views.generic import FormView, TemplateView

from registrations.forms import Step2Form
from registrations.models import GiphouseProfile, Semester, Registration

User = get_user_model()


class Step1View(TemplateView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.warning(request, "You are already logged in", extra_tags='alert alert-success')
            return redirect('home')

        if not Semester.objects.get_current_registration():
            messages.warning(request, "Registrations are currently not open", extra_tags='alert alert-danger')
            return redirect('home')

        return super().dispatch(request, *args, **kwargs)

    template_name = 'registrations/step-1.html'


class Step2View(FormView):
    template_name = 'registrations/step-2.html'
    form_class = Step2Form
    success_url = '/'

    def get_initial(self):
        initial = super(Step2View, self).get_initial()

        try:
            first_name, last_name = self.request.session['github_name'].rsplit(' ', 1)
        except (KeyError, AttributeError):
            first_name, last_name = '', ''

        initial['email'] = self.request.session.get('github_email') or ''
        initial['github_username'] = self.request.session.get('github_username') or ''
        initial['first_name'] = first_name
        initial['last_name'] = last_name

        return initial

    def form_valid(self, form):
        try:
            with transaction.atomic():
                github_id = self.request.session['github_id']
                user = User(username='github_' + str(github_id),
                            first_name=form.cleaned_data['first_name'],
                            last_name=form.cleaned_data['last_name'],
                            email=form.cleaned_data['email'])
                user.save()
                giphouseprofile = GiphouseProfile(
                    user=user,
                    github_username=self.request.session['github_username'],
                    github_id=github_id,
                    student_number=form.cleaned_data['student_number'],
                    role=form.cleaned_data['course'],
                )

                giphouseprofile.save()
                registration = Registration(
                    user=user,
                    preference1=form.cleaned_data['project1'],
                    preference2=form.cleaned_data['project2'],
                    preference3=form.cleaned_data['project3'],
                    comments=form.cleaned_data['comments']
                )
                registration.save()
        except IntegrityError:
            messages.warning(
                self.request, "User already exists", extra_tags='alert alert-danger'
            )
            return redirect('home')
        finally:
            del self.request.session['github_id']
            del self.request.session['github_username']
            del self.request.session['github_name']
            del self.request.session['github_email']

        messages.success(
            self.request, "User created succesfully", extra_tags='alert alert-success'
        )

        login(
            self.request,
            user,
            backend='github_oauth.backends.GithubOAuthBackend',
        )

        return redirect('home')
