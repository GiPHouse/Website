###################################################################################################
# This code is meant to accommodate an INTERACTVE process to create GiPHouse groups.  It is not   #
# meant to be started and then finish with a complete group assignment rolling out; but rather,   #
# it is meant to make suggestions and then allow for manual alterations to requirements and input #
# so that we can still include human judgement in decisions.                                      #
###################################################################################################

import project_data
import engineer_data
import assignment_info
import smt_maker
from colour_codes import *

import csv
import sys
import math
from datetime import datetime
from z3 import *

initialise_colours()

########## STEP 1: reading the projects ##########

# make sure that the given projects file correctly represents this year's projects, or otherwise
# add the projects manually using project_data.add_project
with open("projects.txt", "r", encoding="utf-8") as file:
    project_data.add_projects([f.strip() for f in file.read().splitlines()])

# now set short names for the projects; this is not strictly necessary, but is convenient for
# printing, since otherwise student preferences may for instance get very long
# you will also afterwards be able to refer to a project by its short name
project_data.set_short_name("Automated Water Data Validation", "Water Data")
project_data.set_short_name(
    "Conditional Independence Testing", "Independence Testing"
)
project_data.set_short_name(
    "Digitalization of the Oiconomy Pricing System", "Oiconomy"
)
project_data.set_short_name(
    "Integrating Digital Pathology Tooling with QuPath", "Pathology"
)
project_data.set_short_name(
    "Introduction Scavenger Hunt website", "Scavenger Hunt"
)
project_data.set_short_name("Music Carrier Databas", "Music Carrier")
project_data.set_short_name("My Lifestyle Platform Mobile App", "Lifestyle")
project_data.set_short_name(
    "Portal Genius SAAS Webapplication", "Portal Genius"
)
project_data.set_short_name(
    "RapidReport: an AI-driven radiology reporting", "RapidReport"
)
project_data.set_short_name("Upgrade of ToDI", "ToDI")
project_data.choose_short_names()

# when you are happy, change the year to the current one!
if datetime.now().year != 2026:
    project_data.print_projects()
    sys.exit(0)

########## STEP 2: reading the engineer data ##########

# put in the right filename for the CSV file containing the engineer data
grid = []
with open("test_registrations.csv") as csvfile:
    tablereader = csv.reader(csvfile, delimiter=",")
    for row in tablereader:
        grid.append([entry.strip('"') for entry in row])

# adapt the following code for the current lay-out of the CSV file


def verify_column(index, name):
    namerow = grid[0]
    if index < len(namerow) and namerow[index] == name:
        return index
    print(
        RED
        + 'Column "'
        + name
        + '" is not at index '
        + str(index)
        + "!"
        + RESET
    )
    sys.exit(1)


grid = [grid[0]] + [
    row for row in grid[1:] if row[4] == "Software Engineering"
]

FIRSTNAME = verify_column(0, "First name")
LASTNAME = verify_column(1, "Last name")
PROJECT1 = verify_column(5, "1st project preference")
PROJECT2 = verify_column(6, "2nd project preference")
PROJECT3 = verify_column(7, "3rd project preference")
PARTNER1 = verify_column(8, "1st partner preference")
PARTNER2 = verify_column(9, "2nd partner preference")
PARTNER3 = verify_column(10, "3rd partner preference")
DEVEXP = verify_column(11, "Dev Experience")
MANAGEMENT = verify_column(14, "Management Interest")
NONDUTCH = verify_column(15, "Non-dutch")
TIMESLOT1 = verify_column(16, "Available during scheduled timeslot 1")
TIMESLOT2 = verify_column(17, "Available during scheduled timeslot 2")
TIMESLOT3 = verify_column(18, "Available during scheduled timeslot 3")
TIMESLOT4 = verify_column(19, "Available during scheduled timeslot 4")
TIMESLOT5 = verify_column(20, "Available during scheduled timeslot 5")
TIMESLOT6 = verify_column(21, "Available during scheduled timeslot 6")
TIMESLOT7 = verify_column(22, "Available during scheduled timeslot 7")
TIMESLOT8 = verify_column(23, "Available during scheduled timeslot 8")
TIMESLOT9 = verify_column(24, "Available during scheduled timeslot 9")
TIMESLOT10 = verify_column(25, "Available during scheduled timeslot 10")
NONDA = verify_column(26, "Has problems with signing an NDA")


def get_slots(row):
    slots = []
    if row[TIMESLOT1] == "True":
        slots.append((engineer_data.MONDAY, 1))
    if row[TIMESLOT2] == "True":
        slots.append((engineer_data.MONDAY, 2))
    if row[TIMESLOT3] == "True":
        slots.append((engineer_data.TUESDAY, 1))
    if row[TIMESLOT4] == "True":
        slots.append((engineer_data.TUESDAY, 2))
    if row[TIMESLOT5] == "True":
        slots.append((engineer_data.WEDNESDAY, 1))
    if row[TIMESLOT6] == "True":
        slots.append((engineer_data.WEDNESDAY, 2))
    if row[TIMESLOT7] == "True":
        slots.append((engineer_data.THURSDAY, 1))
    if row[TIMESLOT8] == "True":
        slots.append((engineer_data.THURSDAY, 2))
    if row[TIMESLOT9] == "True":
        slots.append((engineer_data.FRIDAY, 1))
    if row[TIMESLOT10] == "True":
        slots.append((engineer_data.FRIDAY, 2))
    return slots


friend_data = []
for index in range(len(grid) - 1):
    row = grid[index + 1]
    devexp = engineer_data.BEGINNER
    if row[DEVEXP] == "2":
        devexp = engineer_data.INTERMEDIATE
    if row[DEVEXP] == "3":
        devexp = engineer_data.ADVANCED
    slots = get_slots(row)
    engineer_data.add_student(
        row[FIRSTNAME] + " " + row[LASTNAME],
        devexp,
        row[MANAGEMENT] == "True",
        row[NONDUTCH] == "True",
        row[NONDA] == "True",
        slots,
        [row[PROJECT1], row[PROJECT2], row[PROJECT3]],
    )
    partners = [row[PARTNER1], row[PARTNER2], row[PARTNER3]]
    while "" in partners:
        partners.remove("")
    friend_data.append((row[FIRSTNAME] + " " + row[LASTNAME], partners))

# if you see any problems with the student registrations, you can fix them here by directly editing
# the engineer data

# engineer_data.remove_student("man man man") # manager accidentally registered as engineer
# engineer_data.set_management_interest("Let Tim Cook", True)  # has experience with Scrum
# engineer_data.set_level("Permitted Student", engineer_data.JUNIOR) # failed OOP
# engineer_data.set_level("Regular Absentee", engineer_data.JUNIOR) # is abroad for most of the semester
# engineer_data.set_level("Linus Torvalds", engineer_data.PRETTY_GOOD) # codes in free time

# when you are happy, change the year; you can always come back later!
if datetime.now().year != 2026:
    engineer_data.print_students(range(engineer_data.num_students), "")
    engineer_data.print_statistics()
    sys.exit(0)

########## STEP 3: storing friends ##########

# fix friend names and remove names for unregistered people until the friend-storing code below
# succeeds!


def friend_rename(given_name, real_name):
    for i in range(len(friend_data)):
        for j in range(len(friend_data[i][1])):
            if friend_data[i][1][j] == given_name:
                friend_data[i][1][j] = real_name


def friend_remove(given_name):
    for i in range(len(friend_data)):
        if given_name in friend_data[i][1]:
            friend_data[i][1].remove(given_name)


def add_friend(student, friend):
    for i in range(len(friend_data)):
        if friend_data[i][0] == student:
            friend_data[i][1].append(friend)


# rename incorrect names; these are often caused by typos in the registration form
friend_rename("Makr Boute", "Mark Boute")
friend_rename("Cynthia Kopp", "Cynthia Kop")

# remove unregistered referrals
friend_remove("Franz Ferdinand")

# this person indicated additional friends in their comments
add_friend("from", "to")

# friend-storing code; this probably does not need to be altered
failed_friends_registration = False
for student_name, friend_list in friend_data:
    for friend in friend_list:
        if not engineer_data.register_friend(student_name, friend):
            failed_friends_registration = True
if failed_friends_registration:
    sys.exit(1)

########## STEP 4: minimal requirements regardless of goodness ##########

# Initialise the SMT problem with only those timeslots that we consider plausible for assigning to
# a group.  These should be timeslots that enough people have available to at least try making one
# or two teams out of.
smt_maker.initialise(
    [
        (engineer_data.MONDAY, 1),
        (engineer_data.MONDAY, 2),
        (engineer_data.TUESDAY, 1),
        (engineer_data.TUESDAY, 2),
        (engineer_data.WEDNESDAY, 1),
        (engineer_data.WEDNESDAY, 2),
        (engineer_data.THURSDAY, 1),
        (engineer_data.THURSDAY, 2),
        (engineer_data.FRIDAY, 1),
        (engineer_data.FRIDAY, 2),
    ]
)

# directors are only available on Wednesday and Friday, so everyone should get at least one of those timeslots
smt_maker.require_groups_have_at_least_one_slot_among(
    [(engineer_data.WEDNESDAY, 1), (engineer_data.FRIDAY, 2)]
)
# this client cannot do their first meeting on Friday afternoon, but can do it on Thursday afternoon!
# smt_maker.require_group_has_slot("secret-ish", (engineer_data.THURSDAY, 2))
# for the sake of the two managers who cannot attend on those slots, there should be one team with an additional
# Tuesday morning working slot!
smt_maker.require_at_least_number_of_groups_with_slots(
    1, [(engineer_data.TUESDAY, 1)]
)

# this returns the list of all students who are not available at any of the above times
# the second argument indicates whether the function should print these students
tricky_students = engineer_data.query_students_unavailable_at(
    smt_maker.plausible_slots, True
)

# every group is allocated a number of time slots; this requires that everyone in the group is
# available at those slots except for the tricky students (since they can't be)
smt_maker.require_everyone_available_except(tricky_students)
smt_maker.require_groups_have_at_least_one_slot()

# set the size of the groups; by default they're all the same size, but if it's desirable for
# specific projects to have a different number of students, we can set that here
minsize = math.floor(engineer_data.num_students / project_data.num_projects)
maxsize = math.ceil(engineer_data.num_students / project_data.num_projects)
groupsizes = [(minsize, maxsize) for i in range(project_data.num_projects)]
# groupsizes[project_data.get_project_identifier("SmallerProject")] = (6,6)
smt_maker.require_size_boundaries(groupsizes)

engineer_data.print_students(tricky_students, "")

# mark the groups with an NDA, so students who don't want to sign one are not put into these groups
# smt_maker.require_observe_nda(["Classification"])

# check if the problem is solvable with these basic requirements; if not, something is very wrong
# with some inputs, and you need to change them, for example:
# - one of the given timeslots has only a few students, who are only available at that timeslot
# - the group sizes aren't actually feasible as given
if datetime.now().year != 2026:
    assignment = smt_maker.solve()
    if assignment == None:
        print(RED + "Not even the bare basics are satisfiable!" + RESET)
        sys.exit(1)
    print(GREEN + "The basic requirements are satisfiable!" + RESET)
    assignment_info.print_assignment(assignment, None)
    sys.exit(0)

########## STEP 5: setting additional requirements on the composition of groups ##########

preassignment = [None for student in range(engineer_data.num_students)]


def preassign(student, group):
    sid = engineer_data.get_student_identifier(student)
    pid = project_data.get_project_identifier(group)
    preassignment[pid] = sid
    smt_maker.require_student_has_project(sid, pid)


# If there are students who should definitely be in the same group, or definitely not, add these
# requirements here.  You can also pre-assign students to projects here (using the preassign
# function) or require that certain students are NOT in certain projects (using
# smt_maker.require_student_does_not_have_project(student, project))

# these people all have the same tricky availability
# smt_maker.require_together([ "Person One", "Person Two", "Person Three" ])

# You may or may not want to avoid any international students being on their own (it is generally
# nice, but *does* make life harder for the SMT solver, which can make it harder to find a good
# assignment; you can also make individual exceptions)
for student in range(engineer_data.num_students):
    if engineer_data.is_international(student):
        smt_maker.require_together_with_other_international(student)

# If needed, you can also add SMT requirements here directly
# frank = engineer_data.get_student_identifier("Frank Sinatra")  # let's put Frank in a team of 7
# for group in range(project_data.num_projects):
#  smt_maker.add_requirement(Implies(smt_maker.Assignment[frank] == group,
#                                    smt_maker.GroupSize[group] == 7))

# If it doesn't make the problem unsolvable, also leave this rule: it is very annoying to have
# multiple students in a team who cannot be available during any of the scheduled timeslots, so
# we ideally want them separate.
# smt_maker.require_separate(tricky_students)

smt_maker.require_group_is_dutch(
    "Sometimes clients require a Dutch-speaking team"
)

if datetime.now().year != 2026:
    assignment = smt_maker.solve()
    if assignment == None:
        print(RED + "Not even the bare basics are satisfiable!" + RESET)
        sys.exit(1)
    print(GREEN + "The basic requirements are satisfiable!" + RESET)
    assignment_info.print_assignment(assignment, None)
    assignment_info.print_statistics(assignment)
    sys.exit(0)

########## STEP 5a: splitting up friend groups ##########

# We want to avoid groups that largely consist of an existing friend group.  Hence, set
# MAX_PARTNER_GROUP_SIZE to the maximum number of friends that may be in a single group,
# and then inspect the resulting friend groups that are over this limit.  If you think that
# some friendships were missed or should be two-sided when they are currently one-sided, then add
# them *before* this code using engineer_data.register_friend(person1, person2).  You can also
# remove erroneous friendships using engineer_data.deregister_friend(person1, person2).
MAX_PARTNER_GROUP_SIZE = 3
friend_groups = [
    group
    for group in engineer_data.find_friend_groups()
    if len(group) > MAX_PARTNER_GROUP_SIZE
]
friend_groups.sort(key=len, reverse=True)

if datetime.now().year != 2026:
    for group in friend_groups:
        print(
            "["
            + str(len(group))
            + "] "
            + " ; ".join([engineer_data.get_student_name(x) for x in group])
        )

# To split up friend groups, you can either use the separate_group functionality below, or manually
# assign together / separate groups, or even preassign people.  The separate functionality leaves
# the solver free to find its own solution, but might just make the solver process much slower,
# especially when you apply it to larger friend groups.
#
# For preassigning students, you can use
#   engineer_data.print_students(friend_groups[i], "") to see
# the full information of the students in a group, and
#   assignment_info.print_assignment(preassignment, None)
# to see the information on individual groups' needs and popularity.

# engineer_data.print_students(friend_groups[0], "")
# assignment_info.print_assignment(preassignment, None)

# group 0
# we do this to help the solver. Less options = faster solving.
preassign("student", "team")

smt_maker.require_student_does_not_have_project(
    "this can be done for a lot of reasons", "team"
)

# we split up large friend graphs
# group 1
smt_maker.require_together(["a", "b", "c"])
smt_maker.require_together(["d", "e"])
smt_maker.require_together(["f", "g", "h"])
smt_maker.require_separate(["a", "d", "f"])

# the rest are groups of 4 or less, so we'll let the SMT-solver handle it
smt_maker.require_not_all_together(friend_groups[8])
smt_maker.require_not_all_together(friend_groups[9])

# NOTE: the following code could be used for groups of 5 or more if there's no obvious subdivision,
# letting the SMT-solver separate them as it sees fit.  Beware that if the given group is large
# (say, MAX_PARTNER_GROUP_SIZE+3 or more), then this adds quite a few requirements, which is likely
# to make the SMT-solver rather inefficient


# returns [ lst ++ rest | rest is any subgroup of group[start:] that has length size ]
def make_subgroups(group, size, lst, start):
    if size == 0:
        return [lst]
    if start + size == len(group):
        return [lst + group[start:]]
    return make_subgroups(group, size, lst, start + 1) + make_subgroups(
        group, size - 1, lst + [group[start]], start + 1
    )


# subgroups = make_subgroups(friend_groups[4], MAX_PARTNER_GROUP_SIZE+1, [], 0)
# for subgroup in subgroups:
#  smt_maker.require_not_all_together(subgroup)

# let's see if all of this is still satisfiable; change the year to the current if it is!
if datetime.now().year != 2026:
    assignment = smt_maker.solve()
    if assignment == None:
        print(RED + "The group requirements are not satisfiable!" + RESET)
        sys.exit(1)
    print(GREEN + "The group requirements are satisfiable!" + RESET)
    assignment_info.print_assignment(assignment, friend_groups[0])
    assignment_info.print_statistics(assignment)
    sys.exit(0)


########## STEP 6: set minima and maxima for the total group expertise ##########

# Set the minimum and maximum total experience required per project.  Play with these values until
# the SMT solver finds a solution without _too_ much effort.  You may need to come back and fiddle
# with them later as it can have a lot of impact on performance in unexpected ways.

if datetime.now().year != 2026:
    print(
        "Average developer experience:",
        engineer_data.query_average_dev_experience(),
    )
desired_expertise = [(6, 20) for group in range(project_data.num_projects)]


for group in range(project_data.num_projects):
    smt_maker.set_dev_experience_bounds(
        group, desired_expertise[group][0], desired_expertise[group][1]
    )

if datetime.now().year != 2026:
    assignment = smt_maker.solve_with_timeout(180)
    if assignment == None:
        print(RED + "The experience requirements are not satisfiable!" + RESET)
        sys.exit(1)
    print(GREEN + "The experience requirements are satisfiable!" + RESET)
    assignment_info.print_assignment(assignment, None)
    sys.exit(0)

########## STEP 7: minimise unhappiness! ##########

# All students who have at least two timeslots available should be satisfied.
# should_be_satisfied = [ student for student in range(engineer_data.num_students)
#                        if len(engineer_data.get_student_timeslots(student)) >= 2 ]

# All students are happy.
should_be_satisfied = [
    student for student in range(engineer_data.num_students)
]

smt_maker.require_everyone_somewhat_happy(should_be_satisfied)

assignment = None
if datetime.now().year != 2026:
    print(str(datetime.now().minute) + ":" + str(datetime.now().second))
    assignment = smt_maker.solve_with_timeout(600)
    print(str(datetime.now().minute) + ":" + str(datetime.now().second))
    if assignment == None:
        print(
            RED + "The unhappiness requirements are not satisfiable!" + RESET
        )
        sys.exit(1)
    print(GREEN + "The unhappiness requirements are satisfiable!" + RESET)
    assignment_info.print_assignment(assignment, should_be_satisfied)
    assignment_info.print_statistics(assignment)
    sys.exit(0)


########## STEP 8: optimise timeslots ##########

# we would like quite a few teams to have an additional timeslot
smt_maker.require_additional_slot_in(
    16,
    [
        (engineer_data.MONDAY, 1),
        (engineer_data.MONDAY, 2),
        (engineer_data.TUESDAY, 1),
        (engineer_data.TUESDAY, 2),
        (engineer_data.WEDNESDAY, 2),
        (engineer_data.THURSDAY, 1),
        (engineer_data.THURSDAY, 2),
        (engineer_data.FRIDAY, 1),
    ],
)


# again, help the solver
preassign("a", "team")

if datetime.now().year != 2025:
    assignment = smt_maker.solve_with_timeout(300)
    if assignment == None:
        print(RED + "The timeslot requirements are not satisfiable!" + RESET)
        sys.exit(1)
    print(GREEN + "The timeslot requirements are satisfiable!" + RESET)
    assignment_info.print_assignment(assignment, [])
    assignment_info.print_statistics(assignment)


########## STEP 9: make people more happy! ##########

# Now we finally get to make our students as happy as possible!  Adapt the scores below to change
# how the happiness of the various cases is counted.  You can also change happiness for individual
# people.
NOTHING_SCORE = -50
FRIEND_SCORE = 3
PROJECT3 = 3
PROJECT2 = 4
PROJECT1 = 5
FRIENDBONUS = 1  # friend AND favoured project => project score + friend bonus

nothing_score = [
    NOTHING_SCORE for student in range(engineer_data.num_students)
]
friend_score = [FRIEND_SCORE for student in range(engineer_data.num_students)]
project3_score = [PROJECT3 for student in range(engineer_data.num_students)]
project2_score = [PROJECT2 for student in range(engineer_data.num_students)]
project1_score = [PROJECT1 for student in range(engineer_data.num_students)]
friend_bonus = [FRIENDBONUS for student in range(engineer_data.num_students)]

# # they care more for partner preference
# for student in [ "A", "B", "C", "D" ]:
#   identifier = engineer_data.get_student_identifier(student)
#   project3_score[identifier] = 1
#   project2_score[identifier] = 2
#   project1_score[identifier] = 3
#   friend_score[identifier] = 5
#
# # they do not care at all about projects
# for student in [ "Cees van Kooten" ]:
#   identifier = engineer_data.get_student_identifier(student)
#   project3_score[identifier] = 0
#   project2_score[identifier] = 0
#   project1_score[identifier] = 0
#   friend_score[identifier] = 5
#
# # they care more for project preference
# for student in [ "Cynthia Kop" ]:
#   friend_score[engineer_data.get_student_identifier(student)] = 1
#
# # they are happy with anything
# for student in [ "Happy McFay" ]:
#   nothing_score[engineer_data.get_student_identifier(student)] = 0

smt_maker.require_score_definitions(
    nothing_score,
    friend_score,
    friend_bonus,
    project1_score,
    project2_score,
    project3_score,
)
increment = 127
score = -800 - increment

if assignment != None:
    last_good_assignment = assignment
    score = assignment_info.get_score(
        assignment,
        nothing_score,
        friend_score,
        friend_bonus,
        project1_score,
        project2_score,
        project3_score,
    )
    print("Latest score:", score)

while increment >= 1:
    extra = smt_maker.get_minimum_score_requirement(score + increment)
    print(str(datetime.now().minute) + ":" + str(datetime.now().second))
    assignment = smt_maker.solve_with(extra, 120)
    print(str(datetime.now().minute) + ":" + str(datetime.now().second))
    if assignment == None:
        print(
            YELLOW
            + "Could not find an assignment worth at least "
            + str(score + increment)
            + "!"
            + RESET
        )
        increment = math.floor(increment / 2)
    else:
        last_good_assignment = assignment
        score = assignment_info.get_score(
            assignment,
            nothing_score,
            friend_score,
            friend_bonus,
            project1_score,
            project2_score,
            project3_score,
        )
        print(
            GREEN + "Found an assignment scoring " + str(score) + "!" + RESET
        )
        assignment_info.print_assignment(
            assignment, assignment_info.get_happy_students(assignment)
        )
