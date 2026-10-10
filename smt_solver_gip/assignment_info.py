import project_data
import engineer_data
from colour_codes import *

###################################################################################################
# This module contains functionality to query and print information about a given (full or        #
# partial) assignment from students to groups.                                                    #
###################################################################################################


# This returns the slots shared by everyone in the given group (except for those who have nothing
# available)
def get_shared_slots(lst):
    if len(lst) == 0:
        return [(engineer_data.MONDAY, 1), (engineer_data.MONDAY, 2)]
    if len(lst) == 1:
        return engineer_data.get_student_timeslots(lst[0])
    ret = engineer_data.query_shared_timeslots(lst, None)
    if ret != []:
        return ret
    for i in range(len(lst)):
        ret = ret + engineer_data.query_shared_timeslots(
            lst[0:i] + lst[i + 1 :], None
        )
    return list(dict.fromkeys(ret))


def get_slots_info(student_list):
    return ",".join([x[0] + str(x[1]) for x in get_shared_slots(student_list)])


# This returns how many of the students have chosen this group as one of their
# preferred options.
def get_popularity(group_index, student_list):
    return sum(
        [
            1
            if group_index in engineer_data.get_student_preferences(name)
            else 0
            for name in [
                engineer_data.get_student_name(i) for i in student_list
            ]
        ]
    )


def get_student_score(
    student,
    assignment,
    nothing_score,
    friend_score,
    friend_bonus,
    project1_score,
    project2_score,
    project3_score,
):
    student = engineer_data.get_student_identifier(student)
    has_friend = [
        friend
        for friend in engineer_data.get_friends(student)
        if assignment[student] == assignment[friend]
    ] != []
    preferences = engineer_data.get_student_preferences(student)
    ret = 0
    got_project = True
    if len(preferences) > 0 and assignment[student] == preferences[0]:
        ret = project1_score[student]
    elif len(preferences) > 1 and assignment[student] == preferences[1]:
        ret = project2_score[student]
    elif len(preferences) > 2 and assignment[student] == preferences[2]:
        ret = project3_score[student]
    else:
        got_project = False
    if got_project and has_friend:
        ret = max(ret + friend_bonus[student], friend_score[student] + 1)
    elif has_friend:
        ret = friend_score[student]
    elif not got_project:
        ret = nothing_score[student]
    return ret


def get_score(
    assignment,
    nothing_score,
    friend_score,
    friend_bonus,
    project1_score,
    project2_score,
    project3_score,
):
    total = 0
    for student in range(engineer_data.num_students):
        score = get_student_score(
            student,
            assignment,
            nothing_score,
            friend_score,
            friend_bonus,
            project1_score,
            project2_score,
            project3_score,
        )
        total += score
    return total


def get_happy_students(assignment):
    ret = []
    for student in range(engineer_data.num_students):
        if assignment[student] in engineer_data.get_student_preferences(
            student
        ):
            ret.append(student)
        else:
            has_friend = [
                friend
                for friend in engineer_data.get_friends(student)
                if assignment[student] == assignment[friend]
            ] != []
            if has_friend:
                ret.append(student)
    return ret


# This prints information about the given (full or partial) assignment.  If highlight_names is set
# to None, the names of students are not printed.  If it is set to a list, then all assigned
# students are printed; moreover, the students in that list are highlighted.
def print_assignment(assignment, highlight_names):
    groups = [
        [
            student
            for student in range(engineer_data.num_students)
            if assignment[student] == group
        ]
        for group in range(project_data.num_projects)
    ]
    unassigned = [
        i for i in range(engineer_data.num_students) if assignment[i] == None
    ]
    for group in range(project_data.num_projects):
        print(
            project_data.get_project_name(group)
            + (
                ""
                if unassigned == []
                else "[" + str(get_popularity(group, unassigned)) + "]"
            ),
            "working at",
            get_slots_info(groups[group]),
            "with",
            len(groups[group]),
            "engineers ("
            + str(
                len(
                    [
                        x
                        for x in groups[group]
                        if engineer_data.is_international(x)
                    ]
                )
            ),
            "internationals;",
            str(
                len(
                    [
                        x
                        for x in groups[group]
                        if engineer_data.is_management_interested(x)
                    ]
                )
            ),
            "management interested); total level =",
            sum([engineer_data.get_student_level(x) for x in groups[group]]),
        )
        if highlight_names != None:
            highlight_names = [
                engineer_data.get_student_identifier(x)
                for x in highlight_names
            ]
            for sid in groups[group]:
                engineer_data.print_student(sid, " * ", sid in highlight_names)
            print()


def print_statistics(assignment):
    num_pref1 = 0
    num_pref2 = 0
    num_pref3 = 0
    num_withfriend = 0
    for student in range(engineer_data.num_students):
        prefs = engineer_data.get_student_preferences(student)
        group = assignment[student]
        if len(prefs) > 0 and group == prefs[0]:
            num_pref1 += 1
        if len(prefs) > 1 and group == prefs[1]:
            num_pref2 += 1
        if len(prefs) > 2 and group == prefs[2]:
            num_pref3 += 1
    print("Number of students with preference 1:", num_pref1)
    print("Number of students with preference 2:", num_pref2)
    print("Number of students with preference 3:", num_pref3)
    for student in range(engineer_data.num_students):
        has_friend = False
        for friend in engineer_data.get_friends(student):
            if assignment[student] == assignment[friend]:
                has_friend = True
        if has_friend:
            num_withfriend += 1
    print("Number of students with a friend:", num_withfriend)


#  def print_project_popularity():
#    print("Projects and their popularity:")
#    lst = []
#    for i in range(num_projects):
#      count = 0
#      for student in range(num_students):
#        if i in preferences[student]: count = count + 1
#      lst.append((project_names[i], count))
#    lst.sort(key = lambda x:-x[1])
#    for pair in lst:
#      print("  " + pair[0] + ":", pair[1])
