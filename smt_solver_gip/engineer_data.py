###################################################################################################
# This module keeps track of the information we know about engineers: their names, preferences,   #
# projects, availability, experience and other properties.                                        #
###################################################################################################

from colour_codes import *
import project_data

import re
import unicodedata

########## constants ##########
BEGINNER = 0
JUNIOR = 1
INTERMEDIATE = 2
PRETTY_GOOD = 3
ADVANCED = 4

MONDAY = "M"
TUESDAY = "T"
WEDNESDAY = "W"
THURSDAY = "H"
FRIDAY = "F"

########## the student data class ##########


class Student:
    def __init__(
        self,
        name,
        dev_exp,
        management,
        international,
        nonda,
        timeslots,
        preferences,
        splitname,
    ):
        self.name = name
        self.dev_exp = dev_exp
        self.management = management
        self.international = international
        self.nonda = nonda
        self.timeslots = timeslots
        self.preferences = preferences
        self.name_components = splitname


########## global variables ##########

num_students = 0
students = []  # list of student_data elements
friends = []  # maps each student ID to the list of their friends

########## different ways of representing the same student ##########


# if the student with the exact given name exists, this returns their unique identifier
# if not, then this will return None
# if given an identifier,it will be returned unmodified
def get_student_identifier(name):
    if isinstance(name, int):
        return name
    for i in range(num_students):
        if students[i].name == name:
            return i
    return None


# this returns the name of the student with the given unique identifier
# if the identifier does not represent a student, then an error is thrown
def get_student_name(identifier):
    return students[identifier].name


########## adding students ##########


def strip_accents(s):
    return "".join(
        c
        for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    )


# splits the given student name into individual words without accents, which is quite important
# for recognising the not-fully-correct names that other students put in their friend references
def make_components(full_name):
    full_name = strip_accents(full_name.lower())
    return re.split(" |-", full_name)


# adds a student with the given name (a string), developer experience / skill (an integer between
# BEGINNER and ADVANCED), management integest (a boolean), international status (a boolean),
# project preferences (a list of names occurring in project_data), and timeslots (a list of pairs
# (day, slot), with day being MONDAY, TUESDAY, WEDNESDAY, THURSDAY or FRIDAY and slot 1--2
#
# this returns the unique identifier of the student
def add_student(
    name, devexp, management, international, nonda, slots, project_preferences
):
    pos = get_student_identifier(name)
    if pos != None:
        print(
            RED + 'The name "' + name + '" occurs more than once (at indexes',
            pos,
            "and",
            len(students)
            + ").  This means partner preferences cannot be trusted."
            + RESET,
        )
        print(
            "Please repair the issue either directly in the input, or in the function that reads "
            "the input."
        )
    prefs = [
        project_data.get_project_identifier(name)
        for name in project_preferences
    ]
    while None in prefs:
        prefs.remove(None)
    comp = make_components(name)
    students.append(
        Student(
            name, devexp, management, international, nonda, slots, prefs, comp
        )
    )
    global num_students
    num_students = num_students + 1


########## removing and altering students ##########


# removes the student with the given name or identifier; this can only be done before any friends
# are stored in the engineer data
def remove_student(student):
    if friends != []:
        print(
            RED
            + "You cannot remove students once friends are added.  Please move the call "
            "earlier." + RESET
        )
        return
    identifier = get_student_identifier(student)
    students.pop(identifier)
    global num_students
    num_students -= 1


def set_level(student, value):
    identifier = get_student_identifier(student)
    students[identifier].dev_exp = value


def set_management_interest(student, value):
    identifier = get_student_identifier(student)
    students[identifier].management = value


def set_international(student, value):
    identifier = get_student_identifier(student)
    students[identifier].international = value


def set_allow_nda(student, value):
    identifier = get_student_identifier(student)
    students[identifier].nonda = not value


########## recovering student properties ##########


def is_international(student):
    identifier = get_student_identifier(student)
    return students[student].international


def is_management_interested(student):
    identifier = get_student_identifier(student)
    return students[student].management


def is_nda_refusing(student):
    identifier = get_student_identifier(student)
    return students[student].nonda


def get_student_level(student):
    identifier = get_student_identifier(student)
    return students[student].dev_exp


def get_student_timeslots(student):
    identifier = get_student_identifier(student)
    return students[identifier].timeslots


def get_student_preferences(student):
    identifier = get_student_identifier(student)
    return students[identifier].preferences


def get_friends(student):
    identifier = get_student_identifier(student)
    return friends[identifier]


########## storing friends ##########


def sublist(lst1, lst2):
    j = 0
    for i in lst1:
        while j < len(lst2) and lst2[j] != i:
            j = j + 1
        if j >= len(lst2):
            return False
    return True


def find_student_by_name(source, name):
    options = []
    given = make_components(name)
    for student in range(num_students):
        other = students[student].name_components
        if sublist(given, other) or sublist(other, given):
            options.append(student)
    if len(options) == 0:
        print(
            RED + "Error:",
            source,
            'has an unknown friend: "' + name + '".  Please either '
            "rename this friend or remove them." + RESET,
        )
        return None
    if len(options) == 1:
        return options[0]
    ret = get_student_index(name)
    others = ", ".join([students[x].name for x in options if options != ret])
    if ret != None:
        print(
            YELLOW
            + 'Warning: student name "'
            + name
            + '" is ambiguous: any reference to it '
            "could also refer to " + others + "." + RESET
        )
        return ret
    print(
        RED + "Error:",
        source,
        'has an ambiguous friend "' + name + '": this could refer '
        "to any of " + others + "." + RESET,
    )
    return None


def register_friend(student, friend_name):
    # prepare the friends list if we're starting to add friends for the first time
    global friends
    if friends == []:
        friends = [[] for i in range(num_students)]

    sid = get_student_identifier(student)
    friendid = find_student_by_name(get_student_name(sid), friend_name)
    if friendid == None:
        return False
    if friendid not in friends[sid]:
        friends[sid].append(friendid)
    return True


def deregister_friend(student, friend):
    sid = get_student_identifier(student)
    fid = get_student_identifier(friend)
    if fid in friends[sid]:
        friends[sid].remove(fid)


########## discovering and managing friend groups ##########


# helper function to determine a non-directed graph of friendships
def determine_symmetric_friends():
    symmetric_friends = [set() for student in range(num_students)]
    for student in range(num_students):
        for friend in friends[student]:
            symmetric_friends[student].add(friend)
            symmetric_friends[friend].add(student)
    return symmetric_friends


def find_friend_groups():
    symmetric_friends = determine_symmetric_friends()
    friend_groups = []
    handled = set()
    for student in range(num_students):
        if student in handled:
            continue
        group = []
        handled.add(student)
        todo = [student]
        while todo != []:
            cur = todo.pop()
            group.append(cur)
            for other in symmetric_friends[cur]:
                if other not in handled:
                    handled.add(other)
                    todo.append(other)
        if len(group) >= 2:
            friend_groups.append(group)
    return friend_groups


def print_friendships():
    for student in range(num_students):
        if friends[student] != []:
            print(
                students[student].name,
                " likes ",
                ", ".join([students[x].name for x in friends[student]]),
            )


def print_asymetric_friendships():
    for student in range(num_students):
        for friend in friend[student]:
            if student not in friends[friend]:
                print(
                    "Friendship from",
                    students[student].name,
                    "to",
                    students[friend].name,
                    "is asymmetric.",
                )


########## statistics ##########


def query_average_dev_experience():
    total = sum([x.dev_exp for x in students])
    return total / project_data.num_projects


def query_international_count():
    return sum([1 if x.international else 0 for x in students])


def query_management_count():
    return sum([1 if x.management else 0 for x in students])


def query_no_nda_count():
    return sum([1 if x.nonda else 0 for x in students])


def query_available_in_slot_count(slot):
    return sum([1 if slot in x.timeslots else 0 for x in students])


def query_popularity(project):
    pid = project_data.get_project_identifier(project)
    return sum([1 if pid in x.preferences else 0 for x in students])


########## general queries ##########d


def query_students_unavailable_at(slotlist, print_names):
    ret = []
    for student in range(num_students):
        x = students[student]
        available = False
        for slot in slotlist:
            if slot in x.timeslots:
                available = True
                break
        if not available:
            if print_names:
                print(
                    YELLOW
                    + x.name
                    + " is not available at any of the plausible timeslots.  This means "
                    "they will not be considered for the timeslot of their group."
                    + RESET
                )
            ret.append(student)
    return ret


def query_students_only_available_at(slotlist):
    return [
        student
        for student in range(num_students)
        if students[student].timeslots == slotlist
    ]


def query_students_who_like(project):
    pid = project_data.get_project_identifier(project)
    return [i for i in range(num_students) if pid in students[i].preferences]


def query_students_who_are_friends_with(student):
    sid = get_student_identifier(student)
    return [i for i in range(num_students) if sid in friends[i]]


# returns the timeslots within the given initial_list that all students in student_list have
# available; if initial_list is None, then instead the list of all available timeslots for the
# students in that list is returned (but the student_list should be non-empty)
def query_shared_timeslots(student_list, initial_list):
    student_list = [get_student_identifier(x) for x in student_list]
    if initial_list == None:
        initial_list = students[student_list[0]].timeslots
    ret = initial_list
    for student in student_list:
        ret = [x for x in ret if x in students[student].timeslots]
    return ret


########## information printing ##########


def print_student(student, prestring, highlight):
    import csv_loader

    identifier = get_student_identifier(student)
    extra_data, extra_columns = csv_loader.get_extra_data()
    col = BROWN
    if highlight:
        col = YELLOW
    print(
        prestring + col + students[identifier].name + RESET + " likes", end=""
    )
    for i in range(len(students[identifier].preferences)):
        if i != 0:
            print(",", end="")
        project = students[identifier].preferences[i]
        print(" " + project_data.get_project_name(project), end="")
    ccode = ""
    if students[identifier].dev_exp >= ADVANCED:
        ccode = GREEN
    elif students[identifier].dev_exp >= INTERMEDIATE:
        ccode = DARKGREEN
    print(
        " ; " + ccode + "lvl " + str(students[identifier].dev_exp) + RESET,
        end="",
    )
    if students[identifier].management:
        print(" ; " + CYAN + "management" + RESET, end="")
    if students[identifier].international:
        print(" ; " + PURPLE + "international" + RESET, end="")
    if students[identifier].nonda:
        print(" ; " + BRED + "no NDA" + RESET, end="")
    print("; available: ", end="")
    for pair in students[identifier].timeslots:
        print(pair[0] + str(pair[1]), end=" ")
    if friends[identifier] == []:
        print(" (no friends)", end="")
    else:
        print(
            " (friends: "
            + " ; ".join(
                [students[friend].name for friend in friends[identifier]]
            )
            + ")",
            end="",
        )
    if students[identifier].name in extra_data:
        for col in extra_columns:
            print(
                f" ; {col}: {extra_data[students[identifier].name][col]}",
                end="",
            )
    print()


def print_students(lst, prestring):
    for student in lst:
        print_student(student, prestring, False)


# prints an overview of relevant data about the students
def print_statistics():
    print("Number of students:", num_students)
    print("Average dev experience per group:", query_average_dev_experience())
    print("Total number of internationals:", query_international_count())
    print(
        "Total number of management interested students:",
        query_management_count(),
    )
    print(
        "Total number of students who do not want an NDA:",
        query_no_nda_count(),
    )
    for day in [MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY]:
        for block in [1, 2, 3, 4]:
            num = query_available_in_slot_count((day, block))
            if num != 0:
                print(
                    "Total number of students available on "
                    + day
                    + str(block)
                    + ":",
                    num,
                )
