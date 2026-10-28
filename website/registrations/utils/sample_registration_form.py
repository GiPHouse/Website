from projects.models import Project
from courses.models import Course, Semester
from registrations.models.registration import Question, Registrations


class SampleRegistrationForm:
    def __init__(self):
        self.reg = Registrations.objects.create(
            title="Sample Registration",
            semester=Semester.objects.get_or_create_current_semester(),
        )

        current_projects = Project.objects.filter(semester=self.reg.semester)
        if current_projects.exists():
            self.reg.projects.set(current_projects)

        self.first_name = ("First name", Question.TEXT)
        self.last_name = ("Last name", Question.TEXT)
        self.email = ("Email", Question.TEXT)
        self.student_number = ("Student number", Question.TEXT)

        self.course = (
            "Course",
            Question.DROPDOWN,
            [course.name for course in Course.objects.all()],
        )

        self.projects = (
            "Project preferences",
            Question.CHOICELIST,
            [
                project.name
                for project in Project.objects.filter(
                    semester=self.reg.semester
                )
            ],
        )

        self.partners = (
            "Partner preferences",
            Question.TEXTLIST,
        )

        self.devexp = (
            "Dev Experience",
            Question.CHOICE,
            ["Beginner", "Junior", "Intermediate", "Pretty Good", "Advanced"],
        )

        self.gitexp = (
            "Git Experience",
            Question.CHOICE,
            ["Beginner", "Junior", "Intermediate", "Pretty Good", "Advanced"],
        )

        self.scrumexp = (
            "Scrum Experience",
            Question.CHOICE,
            ["Beginner", "Junior", "Intermediate", "Pretty Good", "Advanced"],
        )

        self.management = (
            "Management Interest",
            Question.CHOICE,
            ["Yes", "No"],
        )

        self.nondutch = (
            "Non-dutch",
            Question.CHOICE,
            ["Yes", "No"],
        )

        self.timeslots = (
            "Timeslot availability",
            Question.MULTI,
            [
                "Available during scheduled timeslot 1",
                "Available during scheduled timeslot 2",
                "Available during scheduled timeslot 3",
                "Available during scheduled timeslot 4",
                "Available during scheduled timeslot 5",
                "Available during scheduled timeslot 6",
                "Available during scheduled timeslot 7",
                "Available during scheduled timeslot 8",
                "Available during scheduled timeslot 9",
                "Available during scheduled timeslot 10",
            ],
        )

        self.nonda = (
            "Has problems with signing an NDA",
            Question.CHOICE,
            ["Yes", "No"],
        )

    def get_sample_questions(self):
        sample_questions = []
        for key, value in vars(self).items():
            if key == "reg":
                continue
            if len(value) == 2:
                text, qtype = value
                choices = []
            else:
                text, qtype, choices = value

            sample_questions.append((key, text, qtype, choices))

        return sample_questions
