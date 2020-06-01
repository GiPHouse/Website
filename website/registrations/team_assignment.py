import csv
import logging
import threading
from io import StringIO

from django.urls import reverse

from ortools.sat.python import cp_model

from courses.models import Course

from projects.models import Project

from registrations.models import Registration

from tasks.models import Task

CSV_STRUCTURE = [
    "First name",
    "Last name",
    "Student number",
    "Course",
    "Project name",
    "Non Dutch",
    "Remarks",
    "At least one preference fulfilled",
    "Has preferred project",
    "Project preference 1",
    "Project preference 2",
    "Project preference 3",
    "In project with preferred students",
    "Student preference 1",
    "Student preference 2",
    "Student preference 3",
]


class TeamAssignmentGenerator:
    """Team assignment generator to solve the team assignment as a CSP."""

    def __init__(self, semester):
        """Get all required data to create a team assignment for a certain semester."""
        self.semester = semester
        self.managers = list(
            Registration.objects.filter(semester=semester, course=Course.objects.sdm()).order_by("?").all()
        )
        self.num_managers = len(self.managers)
        self.engineers = list(
            Registration.objects.filter(semester=semester, course=Course.objects.se()).order_by("?").all()
        )
        self.num_engineers = len(self.engineers)
        self.projects = list(Project.objects.filter(semester=semester).order_by("?").all())
        self.num_projects = len(self.projects)

        self.engineers_per_project = list(
            len(range(self.num_engineers)[i :: self.num_projects]) for i in range(self.num_projects)
        )
        self.managers_per_project = list(
            len(range(self.num_managers)[i :: self.num_projects]) for i in range(self.num_projects)
        )
        self.task = Task.objects.create(
            total=1, completed=0, redirect_url=reverse("admin:registrations_employee_changelist")
        )
        self.logger = logging.getLogger("django.automaticteams")

        self.logger.info("Create team constraints")
        self._set_up_model()

    def _set_up_model(self):
        """Set up all boolean variables for a model to solve."""
        self.model = cp_model.CpModel()

        self.assigned_managers = {}
        for r in range(self.num_managers):
            for p in range(self.num_projects):
                self.assigned_managers[(r, p)] = self.model.NewBoolVar(f"assigned_manager{r}_to_project{p}")

        self.assigned_engineers = {}
        for r in range(self.num_engineers):
            for p in range(self.num_projects):
                self.assigned_engineers[(r, p)] = self.model.NewBoolVar(f"assigned_engineer{r}_to_project{p}")

        self._add_constraints()

        self.model.Maximize(sum(self._get_objectives()))

    def generate_team_assignment(self):
        """Try to solve the CSP and return the generated assignment if feasible."""
        solver = cp_model.CpSolver()
        self.logger.info("Solve team constraints")
        status = solver.Solve(self.model)
        self.logger.debug(f"{solver.ResponseStats()}")

        return (
            self._get_project_assignment_from_solved_model(solver)
            if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE
            else []
        )

    def _get_project_assignment_from_solved_model(self, solver):
        """Convert a solved model to a dict for registrations to assigned projects."""
        project_for_registrations = {}
        for p in range(self.num_projects):
            for r in range(self.num_managers):
                if solver.BooleanValue(self.assigned_managers[(r, p)]):
                    project_for_registrations[self.managers[r].pk] = self.projects[p]
                    self.logger.debug(f"Assigned manager \t {self.managers[r].user} \t to \t {self.projects[p]}")
            for r in range(self.num_engineers):
                if solver.BooleanValue(self.assigned_engineers[(r, p)]):
                    project_for_registrations[self.engineers[r].pk] = self.projects[p]
                    self.logger.debug(f"Assigned engineer \t {self.engineers[r].user} \t to \t {self.projects[p]}")

        return project_for_registrations

    def write_csv(self, output, project_for_registrations):
        """Write the result of the team creation to a csv file."""
        writer = csv.writer(output)
        writer.writerow(CSV_STRUCTURE)
        for registration in Registration.objects.filter(
            semester=self.semester, course__in=[Course.objects.se(), Course.objects.sdm()]
        ).order_by("user__first_name", "user__last_name"):
            project = project_for_registrations.get(registration.pk, None)
            partners = [
                Registration.objects.get(pk=reg).user for reg, p in project_for_registrations.items() if p == project
            ]
            project_prefs = [registration.preference1, registration.preference2, registration.preference3]
            student_prefs = {
                registration.partner_preference1_user,
                registration.partner_preference2_user,
                registration.partner_preference3_user,
            }
            writer.writerow(
                [
                    registration.user.first_name,
                    registration.user.last_name,
                    registration.user.student_number,
                    registration.course.name,
                    project.name if project else "",
                    "x" if registration.is_international else "",
                    registration.comments,
                    "x" if project in project_prefs or student_prefs.intersection(partners) else "",
                    project_prefs.index(project) + 1 if project in project_prefs else "",
                    registration.preference1,
                    registration.preference2,
                    registration.preference3,
                    len(student_prefs.intersection(partners)),
                    registration.partner_preference1_user,
                    registration.partner_preference2_user,
                    registration.partner_preference3_user,
                ]
            )

    def execute_solve_task(self):
        """Assign each user to a project and store the output in a task."""
        try:
            project_for_registrations = self.generate_team_assignment()
            if not project_for_registrations:
                self.logger.error("No solution found")
                self.task.fail = True
            else:
                self.logger.info("Create csv output")
                output = StringIO()
                self.write_csv(output, project_for_registrations)
                self.task.data = output.getvalue()
                self.task.success_message = "Successfully assigned all users to a project"
        except Exception as e:
            self.logger.exception(e)
            self.task.fail = True
        self.task.completed = 1
        self.task.save()

    def start_solve_task(self):
        """Start the automatic creation of teams in a background task."""
        thread = threading.Thread(target=self.execute_solve_task)
        thread.start()
        return self.task

    # ----------------------- #
    # MODEL CONSTRAINTS
    # ----------------------- #

    def _add_constraints(self):
        """Get all constraints that are used."""
        self._unique_project_per_registration_constraint()
        self._engineers_managers_per_project_constraint()
        self._1_not_international_per_project_constraint()

    def _unique_project_per_registration_constraint(self):
        """Add the constraint that each registration is assigned at least 1 project."""
        for r in range(self.num_managers):
            self.model.Add(sum(self.assigned_managers[(r, p)] for p in range(self.num_projects)) == 1)
        for r in range(self.num_engineers):
            self.model.Add(sum(self.assigned_engineers[(r, p)] for p in range(self.num_projects)) == 1)

    def _engineers_managers_per_project_constraint(self):
        """Add the constraint that each project has the determined amount of engineers and managers."""
        for p in range(self.num_projects):
            self.model.Add(
                sum(self.assigned_managers[(r, p)] for r in range(self.num_managers)) == self.managers_per_project[p]
            )
        for p in range(self.num_projects):
            self.model.Add(
                sum(self.assigned_engineers[(r, p)] for r in range(self.num_engineers))
                == self.engineers_per_project[p]
            )

    def _1_not_international_per_project_constraint(self):
        """Add the constraint that each project should have at least 1 not-international manager."""
        is_international = {}
        num_internationals = 0
        for r in range(self.num_managers):
            is_international[r] = self.managers[r].is_international
            if self.managers[r].is_international:
                num_internationals += 1

        # Do not add the check if it cannot be fulfilled (if the number of not-internationals is too low to put one
        # in each project)
        if not self.num_managers - num_internationals < self.num_projects:
            for p in range(self.num_projects):
                self.model.Add(
                    sum(self.assigned_managers[(r, p)] and not is_international[r] for r in range(self.num_managers))
                    >= 1
                )

    # ----------------------- #
    # MAXIMIZATION OBJECTIVES
    # ----------------------- #

    def _get_objectives(self):
        """Get all weighted partial objective functions that are used."""
        return [
            (1 * self._project_preference_objective()),
            (1 * self._partner_preference_objective()),
            (1 * self._mixed_programming_experience_objective()),
        ]

    def _project_preference_objective(self):
        """
        Create partial objective function for project preference in project assignment.

        We create a dict that contains for each engineer and manager and project, the value of whether that combination
        is preferred. We then calculate the sum of all fact that are true.

        This value is calculated by in such a way that it is prefered to give 2 people their third preference instead
        of 1 person their first preference. The total value per person is 12, as this is divisible by all possible
        numbers needed.
        """
        manager_preferred_projects = {}
        for r in range(self.num_managers):
            pref_is_none = [
                self.managers[r].preference1 is not None,
                self.managers[r].preference2 is not None,
                self.managers[r].preference3 is not None,
            ]
            num_of_pref = sum(pref_is_none)
            for p in range(self.num_projects):
                if self.managers[r].preference1 == self.projects[p]:
                    manager_preferred_projects[(r, p)] = (12 // num_of_pref) + any(pref_is_none[1:])
                elif self.managers[r].preference2 == self.projects[p]:
                    manager_preferred_projects[(r, p)] = (12 // num_of_pref) + pref_is_none[0] - pref_is_none[2]
                elif self.managers[r].preference3 == self.projects[p]:
                    manager_preferred_projects[(r, p)] = (12 // num_of_pref) - any(pref_is_none[:2])
                else:
                    manager_preferred_projects[(r, p)] = 0

        # Create the objective: engineers must be assigned to the project they prefer
        engineer_preferred_projects = {}
        for r in range(self.num_engineers):
            pref_is_none = [
                self.engineers[r].preference1 is not None,
                self.engineers[r].preference2 is not None,
                self.engineers[r].preference3 is not None,
            ]
            num_of_pref = sum(pref_is_none)
            for p in range(self.num_projects):
                if self.engineers[r].preference1 == self.projects[p]:
                    engineer_preferred_projects[(r, p)] = (12 // num_of_pref) + any(pref_is_none[1:])
                elif self.engineers[r].preference2 == self.projects[p]:
                    engineer_preferred_projects[(r, p)] = (12 // num_of_pref) + pref_is_none[0] - pref_is_none[2]
                elif self.engineers[r].preference3 == self.projects[p]:
                    engineer_preferred_projects[(r, p)] = (12 // num_of_pref) - any(pref_is_none[:2])
                else:
                    engineer_preferred_projects[(r, p)] = 0

        objective = sum(
            manager_preferred_projects[(r, p)] * self.assigned_managers[(r, p)]
            for p in range(self.num_projects)
            for r in range(self.num_managers)
        ) + sum(
            engineer_preferred_projects[(r, p)] * self.assigned_engineers[(r, p)]
            for p in range(self.num_projects)
            for r in range(self.num_engineers)
        )

        return objective

    def _mixed_programming_experience_objective(self):
        """Create partial objective function for mixed programming experience in project assignment."""
        programming_experience_for_engineer = {}

        for r in range(self.num_engineers):
            programming_experience_for_engineer[r] = (
                int(self.engineers[r].experience) if self.engineers[r].experience else 0
            )

        objective = (
            sum(
                (
                    max(
                        programming_experience_for_engineer[r] * self.assigned_engineers[(r, p)]
                        for r in range(self.num_engineers)
                    )
                    - min(
                        programming_experience_for_engineer[r] * self.assigned_engineers[(r, p)]
                        for r in range(self.num_engineers)
                    )
                    # TODO: This is not the best way to measure the variety of programming experience and can be
                    #  improved
                )
                for p in range(self.num_projects)
            )
            if self.num_engineers > 0
            else 0
        )

        return objective

    def _partner_preference_objective(self):
        """
        Create partial objective function for partner preference in project assignment.

        Because we are limited to linear expressions for our  objective functions, we introduce new variables for each
        pair of registrations, that define the fact whether these two people are assigned to the same project. By
        adding constraints to the model, we assure the correct boolean value of those 2 variables.

        Since engineers and managers are assigned and indexed separately, we need to consider 3 separate cases:
        - an engineer being in the same project as another engineer
        - a manager being in the same project as another manager
        - an engineer being in the same project as a manager

        Then, we define a dict that contains for each of these facts, whether it is preferred by a user or not and we
        acknowledge a certain weight to that fact. This weight is calculated by dividing the total amount of weight a
        person gets (12) and dividing it by the amount of preferences it has. Since the 'preferred partner relation'
        is not symmetric, we consider 4 cases here:
        - an engineer being in the same project as a preferred fellow engineer
        - a manager being in the same project as a preferred fellow manager
        - an engineer being in the same project as a preferred manager
        - a manager being in the same project as a preferred engineer

        The objective is then formed by the sum of the 'preferredness' of all the true facts for all assigned managers
        and engineers over the different projects that can be assigned.
        """
        # Set up extra boolean variables for the case: engineer - engineer
        engineer_together_in_project_with_engineer = {}
        for e1 in range(self.num_engineers):
            for e2 in range(e1, self.num_engineers):
                for p in range(self.num_projects):
                    engineer_together_in_project_with_engineer[(e1, e2, p)] = self.model.NewBoolVar(
                        f"engineer_{e1}_together_in_project_{p}_with_engineer_{e2}"
                    )
                    engineer_together_in_project_with_engineer[
                        (e2, e1, p)
                    ] = engineer_together_in_project_with_engineer[(e1, e2, p)]
                    self.model.AddMultiplicationEquality(
                        engineer_together_in_project_with_engineer[(e1, e2, p)],
                        [self.assigned_engineers[(e1, p)], self.assigned_engineers[(e2, p)]],
                    )

        # Set up extra boolean variables for the case: manager - manager
        manager_together_in_project_with_manager = {}
        for m1 in range(self.num_managers):
            for m2 in range(m1, self.num_managers):
                for p in range(self.num_projects):
                    manager_together_in_project_with_manager[(m1, m2, p)] = self.model.NewBoolVar(
                        f"manager_{m1}_together_in_project_{p}_with_manager_{m2}"
                    )
                    manager_together_in_project_with_manager[(m2, m1, p)] = manager_together_in_project_with_manager[
                        (m1, m2, p)
                    ]
                    self.model.AddMultiplicationEquality(
                        manager_together_in_project_with_manager[(m1, m2, p)],
                        [self.assigned_managers[(m1, p)], self.assigned_managers[(m2, p)]],
                    )

        # Set up extra boolean variables for the case: engineer - manager
        engineer_together_in_project_with_manager = {}
        for e in range(self.num_engineers):
            for m in range(self.num_managers):
                for p in range(self.num_projects):
                    engineer_together_in_project_with_manager[(e, m, p)] = self.model.NewBoolVar(
                        f"engineer_{e}_together_in_project_{p}_with_manager_{m}"
                    )
                    self.model.AddMultiplicationEquality(
                        engineer_together_in_project_with_manager[(e, m, p)],
                        [self.assigned_engineers[(e, p)], self.assigned_managers[(m, p)]],
                    )

        # Calculate the preferred partners for the case: engineer - engineer
        engineer_preferred_partner_engineers = {}
        for reg in range(self.num_engineers):
            for partner in range(self.num_engineers):
                num_pref = sum(
                    pref is not None
                    for pref in [
                        self.engineers[reg].partner_preference1_user,
                        self.engineers[reg].partner_preference2_user,
                        self.engineers[reg].partner_preference3_user,
                    ]
                )
                if num_pref == 0:
                    engineer_preferred_partner_engineers[(reg, partner)] = 0
                else:
                    engineer_preferred_partner_engineers[(reg, partner)] = (
                        12
                        // num_pref
                        * int(
                            self.engineers[reg].partner_preference1_user == self.engineers[partner].user
                            or self.engineers[reg].partner_preference2_user == self.engineers[partner].user
                            or self.engineers[reg].partner_preference3_user == self.engineers[partner].user
                        )
                    )

        # Calculate the preferred partners for the case: manager - manager
        manager_preferred_partner_managers = {}
        for reg in range(self.num_managers):
            for partner in range(self.num_managers):
                num_pref = sum(
                    pref is not None
                    for pref in [
                        self.managers[reg].partner_preference1_user,
                        self.managers[reg].partner_preference2_user,
                        self.managers[reg].partner_preference3_user,
                    ]
                )
                if num_pref == 0:
                    manager_preferred_partner_managers[(reg, partner)] = 0
                else:
                    manager_preferred_partner_managers[(reg, partner)] = (
                        12
                        // num_pref
                        * int(
                            self.managers[reg].partner_preference1_user == self.managers[partner].user
                            or self.managers[reg].partner_preference2_user == self.managers[partner].user
                            or self.managers[reg].partner_preference3_user == self.managers[partner].user
                        )
                    )

        # Calculate the preferred partners for the case: engineer - manager
        engineer_preferred_partner_managers = {}
        for reg in range(self.num_engineers):
            for partner in range(self.num_managers):
                num_pref = sum(
                    pref is not None
                    for pref in [
                        self.engineers[reg].partner_preference1_user,
                        self.engineers[reg].partner_preference2_user,
                        self.engineers[reg].partner_preference3_user,
                    ]
                )
                if num_pref == 0:
                    engineer_preferred_partner_managers[(reg, partner)] = 0
                else:
                    engineer_preferred_partner_managers[(reg, partner)] = (
                        12
                        // num_pref
                        * int(
                            self.engineers[reg].partner_preference1_user == self.managers[partner].user
                            or self.engineers[reg].partner_preference2_user == self.managers[partner].user
                            or self.engineers[reg].partner_preference3_user == self.managers[partner].user
                        )
                    )

        # Calculate the preferred partners for the case: manager - engineer
        manager_preferred_partner_engineers = {}
        for reg in range(self.num_managers):
            for partner in range(self.num_engineers):
                num_pref = sum(
                    pref is not None
                    for pref in [
                        self.managers[reg].partner_preference1_user,
                        self.managers[reg].partner_preference2_user,
                        self.managers[reg].partner_preference3_user,
                    ]
                )
                if num_pref == 0:
                    manager_preferred_partner_engineers[(reg, partner)] = 0
                else:
                    manager_preferred_partner_engineers[(reg, partner)] = (
                        12
                        // num_pref
                        * int(
                            self.managers[reg].partner_preference1_user == self.engineers[partner].user
                            or self.managers[reg].partner_preference2_user == self.engineers[partner].user
                            or self.managers[reg].partner_preference3_user == self.engineers[partner].user
                        )
                    )

        # Calculate the objective
        objective = (
            sum(
                engineer_preferred_partner_engineers[(e1, e2)]
                * engineer_together_in_project_with_engineer[(e1, e2, p)]
                for e1 in range(self.num_engineers)
                for e2 in range(self.num_engineers)
                for p in range(self.num_projects)
            )
            + sum(
                manager_preferred_partner_managers[(m1, m2)] * manager_together_in_project_with_manager[(m1, m2, p)]
                for m1 in range(self.num_managers)
                for m2 in range(self.num_managers)
                for p in range(self.num_projects)
            )
            + sum(
                engineer_preferred_partner_managers[(e, m)] * engineer_together_in_project_with_manager[(e, m, p)]
                for e in range(self.num_engineers)
                for m in range(self.num_managers)
                for p in range(self.num_projects)
            )
            + sum(
                manager_preferred_partner_engineers[(m, e)] * engineer_together_in_project_with_manager[(e, m, p)]
                for m in range(self.num_managers)
                for e in range(self.num_engineers)
                for p in range(self.num_projects)
            )
        )

        return objective
