###################################################################################################
# This module keeps track of the projects that are known to us.  Most ipmortantly, it allows us   #
# to distinguish projects using both short names, full names and identifier.                      #
###################################################################################################

from colour_codes import *

num_projects = 0
full_names = []
short_names = []


# add a project to the list of projects
def add_project(full_name):
    if full_name in full_names:
        print(
            RED + "Error: duplicate definition of project " + full_name + RESET
        )
    full_names.append(full_name)
    short_names.append(full_name)
    global num_projects
    num_projects = num_projects + 1


# adds all the projects in the given list
def add_projects(full_name_list):
    for name in full_name_list:
        if name != "":
            add_project(name)


# indicates a shorter version of the given group name, used for printing, but also to easily
# refer tp the group
def set_short_name(full_name, short_name):
    if short_name not in full_name:
        print(
            RED
            + "The short name "
            + short_name
            + " does not occur in the full project name "
            + full_name
            + "!"
            + RESET
        )
    matches = [f for f in full_names if short_name in f]
    if len(matches) != 1:
        print(
            RED
            + "The short name "
            + short_name
            + " occurs in multiple full project names: "
            + ", ".join(matches)
            + "."
            + RESET
        )
    short_names[full_names.index(full_name)] = short_name


# this automatically assigns a short name to each group that doesn't have one yet
def choose_short_names():
    for i in range(num_projects):
        if short_names[i] != full_names[i]:
            continue
        for component in full_names[i].split():
            matches = [f for f in full_names if component in f]
            if len(matches) == 1:
                short_names[i] = component
                break


def print_projects():
    print("Projects:")
    for i in range(num_projects):
        if short_names[i] == full_names[i]:
            print(" * " + full_names[i])
        else:
            print(" * " + short_names[i] + " (" + full_names[i] + ")")


# This returns the unique identifier for the project with the given name, if any.
# If no such project is defined, it instead prints an error message and returns None.
def get_project_identifier(name):
    if isinstance(name, int):
        return name
    if name in short_names:
        return short_names.index(name)
    if name in full_names:
        return full_names.index(name)
    matches = [i for i in range(num_projects) if short_names[i] in name]
    if len(matches) == 1:
        return matches[0]
    matches = [i for i in range(num_projects) if full_names[i] in name]
    if len(matches) == 1:
        return matches[0]
    # if name != "": print(RED + "The project \"" + name + "\" could not be (uniquely) identified.")
    return None


# returns the short project name for the project with the given identifier (which must exist)
def get_project_name(identifier):
    if isinstance(identifier, str):
        identifier = get_project_identifier(name)
    return short_names[identifier]
