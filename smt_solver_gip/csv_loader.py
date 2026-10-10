import csv
import ast

import engineer_data
import project_data
from colour_codes import *
from collections import defaultdict

EXPECTED_COLUMNS = [
    "First name",
    "Last name",
    "Student number",
    "GitHub username",
    "Course",
    "project preferences",
    "partner preferences",
    "Dev Experience",
    "Git Experience",
    "Scrum Experience",
    "Management Interest",
    "Non-dutch",
    "Availablility timeslots",
    "Has problems with signing an NDA",
    "Registration Comments",
]

EXPERIENCE_COLUMNS = [
    "Dev Experience",
    "Git Experience",
    "Scrum Experience",
]

VALID_COURSES = [
    "Software Engineering",
    "System Development Management",
    "Software Development Entrepreneurship",
]


def parse_exp(value):
    if value == "Beginner":
        return engineer_data.BEGINNER
    elif value == "Junior":
        return engineer_data.JUNIOR
    elif value == "Intermediate":
        return engineer_data.INTERMEDIATE
    elif value == "Pretty Good":
        return engineer_data.PRETTY_GOOD
    elif value == "Advanced":
        return engineer_data.ADVANCED
    return engineer_data.BEGINNER


def parse_booleans(value):
    if value in ("True", "Yes"):
        return True
    elif value in ("False", "No"):
        return False
    return False


def parse_timetable(row):
    slots = []
    raw = row["Availablility timeslots"].strip()
    try:
        booleans = ast.literal_eval(raw)
    except ValueError, SyntaxError:
        return slots
    mapping = [
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
    for i, available in enumerate(booleans):
        if available and i < len(mapping):
            slots.append(mapping[i])
    return slots


def verify_columns(header):
    missing = [col for col in EXPECTED_COLUMNS if col not in header]
    if missing:
        print(f"{RED}Error: Missing columns: {', '.join(missing)}{RESET}")


def verify_row(row):
    errors = []
    name = row["First name"] + " " + row["Last name"]

    if row["Course"] not in VALID_COURSES:
        errors.append(f"Invalid course '{row['Course']}' for student {name}")

    for pref in [
        p.strip() for p in row["project preferences"].split(",") if p.strip()
    ]:
        if (
            pref not in project_data.full_names
            and pref not in project_data.short_names
        ):
            errors.append(
                f"Invalid project preference '{pref}' for student {name}"
            )

    for col in EXPERIENCE_COLUMNS:
        if row[col] and row[col] not in [
            "Beginner",
            "Junior",
            "Intermediate",
            "Pretty Good",
            "Advanced",
        ]:
            errors.append(
                f"Invalid experience level '{row[col]}' in column {col} for student {name}"
            )

    for col in [
        "Management Interest",
        "Non-dutch",
        "Has problems with signing an NDA",
    ]:
        if row[col] not in ["True", "False", "Yes", "No"]:
            errors.append(
                f"Invalid boolean value '{row[col]}' in column {col} for student {name}"
            )

    return name, errors


managers = []
friend_data = []
extra_columns = []
extra_data = {}
all_errors = defaultdict(list)


def load_registrations(filename):
    global extra_columns
    with open(filename, "r") as csvfile:
        reader = csv.DictReader(csvfile)
        header = reader.fieldnames
        extra_columns = [col for col in header if col not in EXPECTED_COLUMNS]
        verify_columns(header)
        for row in reader:
            name, errors = verify_row(row)
            if errors:
                all_errors[name].extend(errors)
            elif row["Course"] == "Software Engineering":
                engineer_data.add_student(
                    name,
                    parse_exp(row["Dev Experience"]),
                    parse_booleans(row["Management Interest"]),
                    parse_booleans(row["Non-dutch"]),
                    parse_booleans(row["Has problems with signing an NDA"]),
                    parse_timetable(row),
                    [
                        p.strip()
                        for p in row["project preferences"].split(",")
                        if p.strip()
                    ],
                )
                partners = [
                    p.strip()
                    for p in row["partner preferences"].split("§")
                    if p.strip()
                ]
                friend_data.append((name, partners))
                if extra_columns:
                    extra_data[name] = {col: row[col] for col in extra_columns}
            else:
                managers.append(row)

    if all_errors:
        print(
            f"{YELLOW}The following students were skipped due to invalid data:{RESET}"
        )
        for name, errors in all_errors.items():
            print(f"{YELLOW}  {name}:{RESET}")
            for error in errors:
                print(f"{YELLOW}    - {error}{RESET}")

        skipped = set(all_errors.keys())
        for i in range(len(friend_data)):
            friend_data[i] = (
                friend_data[i][0],
                [f for f in friend_data[i][1] if f not in skipped],
            )


def get_friend_data():
    return friend_data


def get_managers():
    return managers


def get_extra_data():
    return extra_data, extra_columns


def print_manager(manager, prestring, highlight):
    col = BROWN
    if highlight:
        col = YELLOW
    name = manager["First name"] + " " + manager["Last name"]
    print(prestring + col + name + RESET + " likes", end="")
    prefs = [
        p.strip()
        for p in manager["project preferences"].split(",")
        if p.strip()
    ]
    for i in range(len(prefs)):
        if i != 0:
            print(",", end="")
        print(" " + prefs[i], end="")
    exp = parse_exp(manager["Dev Experience"])
    ccode = ""
    if exp >= engineer_data.ADVANCED:
        ccode = GREEN
    elif exp >= engineer_data.INTERMEDIATE:
        ccode = DARKGREEN
    print(" ; " + ccode + "lvl " + str(exp) + RESET, end="")
    if parse_booleans(manager["Management Interest"]):
        print(" ; " + CYAN + "management" + RESET, end="")
    if parse_booleans(manager["Non-dutch"]):
        print(" ; " + PURPLE + "international" + RESET, end="")
    if parse_booleans(manager["Has problems with signing an NDA"]):
        print(" ; " + BRED + "no NDA" + RESET, end="")
    slots = parse_timetable(manager)
    print("; available: ", end="")
    for pair in slots:
        print(pair[0] + str(pair[1]), end=" ")
    for col in extra_columns:
        print(f" ; {col}: {manager[col]}", end="")
    print()


def print_managers(lst, prestring):
    for manager in lst:
        print_manager(manager, prestring, False)
