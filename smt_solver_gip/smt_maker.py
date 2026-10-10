import project_data
import engineer_data

from z3 import *
from colour_codes import *

###################################################################################################
# This module is responsible for building the SMT requirements and running the solver.            #
###################################################################################################

# essentially a constant: set at initialisation and then never changed
plausible_slots = []

# the SMT variables that multiple functions work with
Assignment = []
GroupSize = []
GroupHasSlot = []
HasFriend = []
StudentScore = []
TotalScore = None

# the list of requirements we will steadily build up
reqs = []

########## setting up variables and definitions ##########


# Call this first: this initalises the key variables, based on the number of students and groups,
# as well as the slots we consider plausible for groups to work together at
def initialise(possible_slots):
    # the main variables that keep track of which student is assigned which group
    global Assignment
    Assignment = [
        Int("project_for_%d" % i) for i in range(engineer_data.num_students)
    ]
    for i in range(engineer_data.num_students):
        reqs.append(
            And(
                [0 <= Assignment[i], Assignment[i] < project_data.num_projects]
            )
        )
    # an integer representing the size of the group
    for group in range(project_data.num_projects):
        GroupSize.append(Int("group_size_%d" % group))
        reqs.append(
            GroupSize[group]
            == Sum(
                [
                    If(Assignment[student] == group, 1, 0)
                    for student in range(engineer_data.num_students)
                ]
            )
        )
    # the timeslots in which the students in the group are expected to be available
    global plausible_slots
    plausible_slots = possible_slots
    for group in range(project_data.num_projects):
        GroupHasSlot.append(
            [
                Bool("slot_%d_%s%d" % (group, pair[0], pair[1]))
                for pair in possible_slots
            ]
        )
    # whether or not each student has a friend
    global HasFriend
    HasFriend = [
        Bool("has_friend_%d" % i) for i in range(engineer_data.num_students)
    ]
    for student in range(engineer_data.num_students):
        friends = engineer_data.get_friends(student)
        if len(friends) == 0:
            reqs.append(Not(HasFriend[student]))
        elif len(friends) == 1:
            reqs.append(
                HasFriend[student]
                == (Assignment[student] == Assignment[friends[0]])
            )
        else:
            reqs.append(
                HasFriend[student]
                == Or(
                    [
                        Assignment[student] == Assignment[friend]
                        for friend in friends
                    ]
                )
            )
    # their score counting towards the goodness of an assignment
    global StudentScore
    StudentScore = [
        Int("student_score_%d" % i) for i in range(engineer_data.num_students)
    ]
    global TotalScore
    TotalScore = Int("totalscore")


# allow outside callers to manually add sophisticated requirements
# (this creates coupling so should probably be avoided for anything long-term, but in practice we
# may have very concrete requirements that only apply during a given year, and the most convenient
# way to deal with them is just to add them in assigner.py directly)
def add_requirement(req):
    reqs.append(req)


########## basic requirements ##########


# require that a group does not contain any members not available at its scheduled timeslots,
# except perhaps for the tricky members; we do not require that if all members are available at a
# given time then the slot is marked as true, but this will typically be set anyway while optimising
def require_everyone_available_except(tricky_students):
    tricky_students = [
        engineer_data.get_student_identifier(x) for x in tricky_students
    ]
    for group in range(project_data.num_projects):
        for student in range(engineer_data.num_students):
            if student in tricky_students:
                continue
            slots = engineer_data.get_student_timeslots(student)
            for i in range(len(plausible_slots)):
                if plausible_slots[i] not in slots:
                    reqs.append(
                        Implies(
                            Assignment[student] == group,
                            Not(GroupHasSlot[group][i]),
                        )
                    )


# require that the size of each group is in the range given by list[group]
def require_size_boundaries(lst):
    for group in range(project_data.num_projects):
        minsize = lst[group][0]
        maxsize = lst[group][1]
        reqs.append(
            And(minsize <= GroupSize[group], GroupSize[group] <= maxsize)
        )


def require_groups_have_at_least_one_slot():
    for group in range(project_data.num_projects):
        reqs.append(
            Or([GroupHasSlot[group][i] for i in range(len(plausible_slots))])
        )


########## requirements on people being together or not ##########


# require that everyone in the given list (which may be identifiers or names) is in a
# different project
def require_separate(student_list):
    if len(student_list) > project_data.num_projects:
        print(
            RED
            + "I cannot separate all students in a list of length "
            + len(student_list)
            + "!"
            + RESET
        )
        return
    student_list = [
        engineer_data.get_student_identifier(x) for x in student_list
    ]
    for i in range(len(student_list)):
        for j in range(i + 1, len(student_list)):
            reqs.append(
                Assignment[student_list[i]] != Assignment[student_list[j]]
            )


# require that everyone in the given list (which may be identifiers or names) is in the
# same project
def require_together(student_list):
    student_list = [
        engineer_data.get_student_identifier(x) for x in student_list
    ]
    for i in range(1, len(student_list)):
        reqs.append(Assignment[student_list[0]] == Assignment[student_list[i]])
    shared = engineer_data.query_shared_timeslots(
        student_list, plausible_slots
    )
    if shared == []:
        print(
            RED
            + "There is no suitable timeslot shared by "
            + ", ".join(
                [engineer_data.get_student_name(x) for x in student_list]
            )
            + "."
            + RESET
        )


def require_not_all_together(student_list):
    lst = [engineer_data.get_student_identifier(x) for x in student_list]
    reqs.append(Or([Assignment[x] != Assignment[lst[0]] for x in lst[1:]]))


def require_together_with_friend(student_name):
    reqs.append(HasFriend[engineer_data.get_student_identifier(student_name)])


def require_together_with_other_international(student):
    student = engineer_data.get_student_identifier(student)
    internationals = [
        x
        for x in range(engineer_data.num_students)
        if engineer_data.is_international(x) and x != student
    ]
    reqs.append(
        Or([Assignment[student] == Assignment[i] for i in internationals])
    )


########## requirements on assignment ##########


def require_student_has_project(student, project):
    sid = engineer_data.get_student_identifier(student)
    pid = project_data.get_project_identifier(project)
    reqs.append(Assignment[sid] == pid)


def require_student_does_not_have_project(student, project):
    sid = engineer_data.get_student_identifier(student)
    pid = project_data.get_project_identifier(project)
    reqs.append(Assignment[sid] != pid)


def require_observe_nda(nda_projects):
    for project in nda_projects:
        project = project_data.get_project_identifier(project)
        for student in range(engineer_data.num_students):
            if engineer_data.is_nda_refusing(student):
                reqs.append(Assignment[student] != project)


def require_group_is_dutch(groupname):
    group = project_data.get_project_identifier(groupname)
    for student in range(engineer_data.num_students):
        if engineer_data.is_international(student):
            reqs.append(Assignment[student] != group)


########## requirements on experience ##########


def set_dev_experience_bounds(group, minlevel, maxlevel):
    students_with_exp = [
        (x, engineer_data.get_student_level(x))
        for x in range(engineer_data.num_students)
    ]
    students_with_exp = [(x, e) for (x, e) in students_with_exp if e > 0]
    countvar = Int("experience_for_%d" % group)
    reqs.append(minlevel <= countvar)
    reqs.append(countvar <= maxlevel)
    reqs.append(
        countvar
        == Sum(
            [If(Assignment[x] == group, e, 0) for (x, e) in students_with_exp]
        )
    )


########## requirements on slots ##########


def require_has_some_slot_in(group, slots):
    slotindexes = [plausible_slots.index(x) for x in slots]
    reqs.append(Or([GroupHasSlot[group][i] for i in slotindexes]))


def require_groups_have_at_least_one_slot_among(slots):
    for group in range(project_data.num_projects):
        reqs.append(
            Or(
                [
                    GroupHasSlot[group][i]
                    for i in range(len(plausible_slots))
                    if plausible_slots[i] in slots
                ]
            )
        )


def require_group_has_slot(groupname, slot):
    for i in range(len(plausible_slots)):
        if plausible_slots[i] == slot:
            reqs.append(
                GroupHasSlot[project_data.get_project_identifier(groupname)][i]
            )


def require_at_least_number_of_groups_with_slots(count, slots):
    slotindexes = [plausible_slots.index(x) for x in slots]
    slotstring = "".join([x[0] + str(x[1]) for x in slots])
    HasTheseSlots = [
        Int("goodslotbit_%d" % i) for i in range(project_data.num_projects)
    ]
    for group in range(project_data.num_projects):
        reqs.append(HasTheseSlots[group] <= 1)
        for i in slotindexes:
            reqs.append(Or(GroupHasSlot[group][i], HasTheseSlots[group] == 0))
    reqs.append(
        Sum(
            [
                HasTheseSlots[group]
                for group in range(project_data.num_projects)
            ]
        )
        >= count
    )


def require_additional_slot_in(count, slots):
    slotindexes = [plausible_slots.index(x) for x in slots]
    HasExtra = [
        Int("hasextra_%d" % i) for i in range(project_data.num_projects)
    ]
    for group in range(project_data.num_projects):
        reqs.append(HasExtra[group] <= 1)
        reqs.append(
            Or(
                HasExtra[group] == 0,
                Or([GroupHasSlot[group][i] for i in slotindexes]),
            )
        )
    reqs.append(
        Sum([HasExtra[group] for group in range(project_data.num_projects)])
        >= count
    )


def require_number_of_groups_with_consecutive_slot(count, consecutive_options):
    HasConsecutiveSlot = [
        Int("goodslot_%d" % i) for i in range(project_data.num_projects)
    ]
    consecutive_options = [
        [plausible_slots.index(x) for x in option]
        for option in consecutive_options
    ]
    for group in range(project_data.num_projects):
        reqs.append(HasConsecutiveSlot[group] <= 1)
        premiselist = [
            Or([Not(GroupHasSlot[group][i]) for i in option])
            for option in consecutive_options
        ]
        premise = And(premiselist)
        if len(premiselist) == 1:
            premise = premiselist[0]
        reqs.append(Implies(premise, HasConsecutiveSlot[group] == 0))
    reqs.append(
        Sum(
            [
                HasConsecutiveSlot[group]
                for group in range(project_data.num_projects)
            ]
        )
        >= count
    )


########## requirements on not being unhappy ##########


def require_somewhat_happy(student):
    reqs.append(
        Or(
            [HasFriend[student]]
            + [
                Assignment[student] == pref
                for pref in engineer_data.get_student_preferences(student)
            ]
        )
    )


def require_everyone_somewhat_happy(students):
    for student in students:
        require_somewhat_happy(student)


def require_preference_minimum(num, above):
    HasAPreference = [
        Int("haspref_%d" % i) for i in range(engineer_data.num_students)
    ]
    for student in range(engineer_data.num_students):
        reqs.append(HasAPreference[student] <= 1)
        preferences = engineer_data.get_student_preferences(student)
        reqs.append(
            Or(
                HasAPreference[student] == 0,
                Or(
                    [
                        Assignment[student] == preferences[i]
                        for i in range(above)
                    ]
                ),
            )
        )
    reqs.append(
        Sum(
            [
                HasAPreference[student]
                for student in range(engineer_data.num_students)
            ]
        )
        >= num
    )


########## requirements on the scoring ##########


def require_score_definition_for(
    student, nothing_score, friend_score, friend_bonus, proj_scores
):
    reqs.append(nothing_score <= StudentScore[student])
    reqs.append(
        StudentScore[student]
        <= max(friend_score + 1, proj_scores[0] + friend_bonus)
    )
    preferences = engineer_data.get_student_preferences(student)
    for i in range(min(len(preferences), len(proj_scores))):
        reqs.append(
            Implies(
                And(HasFriend[student], Assignment[student] == preferences[i]),
                StudentScore[student]
                == max(proj_scores[i] + friend_bonus, friend_score + 1),
            )
        )
        reqs.append(
            Implies(
                And(
                    Not(HasFriend[student]),
                    Assignment[student] == preferences[i],
                ),
                StudentScore[student] == proj_scores[i],
            )
        )
    reqs.append(
        Implies(
            And([Assignment[student] != pref for pref in preferences]),
            StudentScore[student]
            == If(HasFriend[student], friend_score, nothing_score),
        )
    )


def require_score_definitions(
    nothing_scores,
    friend_scores,
    friend_bonuses,
    project1_scores,
    project2_scores,
    project3_scores,
):
    for student in range(engineer_data.num_students):
        require_score_definition_for(
            student,
            nothing_scores[student],
            friend_scores[student],
            friend_bonuses[student],
            [
                project1_scores[student],
                project2_scores[student],
                project3_scores[student],
            ],
        )
    reqs.append(
        TotalScore
        == Sum(
            [
                StudentScore[student]
                for student in range(engineer_data.num_students)
            ]
        )
    )


def get_minimum_score_requirement(num):
    return [TotalScore >= num]


########## solving ##########


# find an assignment for the requirements that are currently stored along with the given
# requirements, or returns None if no such assignment exists
def solve_with(extra, timeout):
    s = Solver()
    s.add(reqs + extra)
    s.set("timeout", 1000 * timeout)
    if s.check() != sat:
        return None
    model = s.model()
    return [
        model.evaluate(Assignment[student], model_completion=True).as_long()
        for student in range(engineer_data.num_students)
    ]


# find an assignment for the requirements that are currently stored, or returns None if the problem
# is unsatisfiable
def solve():
    return solve_with([], 60)


def solve_with_timeout(timeout):
    return solve_with([], timeout)
