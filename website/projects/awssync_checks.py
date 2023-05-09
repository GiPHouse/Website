from __future__ import annotations

from projects.awssync_structs import AWSTree


class Checks:
    """Class for pipeline checks."""

    def check_members_in_correct_iteration(self, AWSdata: AWSTree) -> None:
        """Check if the data from the member tag matches the semester OU it is in."""
        emails_inconsistent_accounts = [
            member.project_email
            for iteration in AWSdata.iterations
            for member in iteration.members
            if member.project_semester != iteration.name
        ]

        if emails_inconsistent_accounts:
            raise Exception(
                f"There are members in a course iteration OU with an inconsistent course iteration tag.\
                      Inconsistent names are {emails_inconsistent_accounts}"
            )

    def check_double_iteration_names(self, AWSdata: AWSTree) -> None:
        """Check if there are multiple OU's with the same name in AWS."""
        names = [iteration.name for iteration in AWSdata.iterations]
        duplicates = [iteration_name for iteration_name in set(names) if names.count(iteration_name) > 1]

        if duplicates:
            raise Exception(
                f"There are multiple course iteration OUs with the same name. Duplicates are: {duplicates}"
            )
