###################################################################################################
# This code is meant to accommodate an INTERACTVE process to create GiPHouse groups.  It is not   #
# meant to be started and then finish with a complete group assignment rolling out; but rather,   #
# it is meant to make suggestions and then allow for manual alterations to requirements and input #
# so that we can still include human judgement in decisions.                                      #
###################################################################################################

import project_data
import engineer_data
import csv_loader
from colour_codes import *

import sys
from datetime import datetime

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

csv_loader.load_registrations("test_registrations.csv")

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

friend_data = csv_loader.get_friend_data()


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
# friend_rename("Alice Johson", "Alice Johnson")

# remove unregistered referrals
friend_remove("Alice Johson")

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

engineer_data.print_students(range(engineer_data.num_students), " * ")

# csv_loader.print_managers(csv_loader.get_managers(), " * ")
