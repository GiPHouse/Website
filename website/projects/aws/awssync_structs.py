from __future__ import annotations


class SyncData:
    """Structure for AWS giphouse sync data."""

    def __init__(self, project_email: str, project_slug: str) -> None:
        """Create SyncData instance."""
        self.project_email = project_email
        self.project_slug = project_slug

    def __eq__(self, other: SyncData) -> bool:
        """Overload equals for SyncData type."""
        if not isinstance(other, SyncData):
            raise TypeError("Must compare to object of type SyncData")
        return self.project_email == other.project_email and self.project_slug == other.project_slug

    def __repr__(self) -> str:
        """Overload to repr function for SyncData type."""
        return f"SyncData('{self.project_email}', '{self.project_slug}')"


class Iteration:
    """Datatype for AWS data in the Course iteration OU."""

    def __init__(self, name: str, ou_id: str, members: list[SyncData]) -> None:
        """Initialize Iteration object."""
        self.name = name
        self.ou_id = ou_id
        self.members = members

    def __repr__(self) -> str:
        """Overload to repr function for Iteration datatype."""
        return f"Iteration('{self.name}', '{self.ou_id}', {self.members})"

    def __eq__(self, other: Iteration) -> bool:
        """Overload equals operator for Iteration objects."""
        if not isinstance(other, Iteration):
            raise TypeError("Must compare to object of type Iteration")
        return self.name == other.name and self.ou_id == other.ou_id and self.members == other.members


class AWSTree:
    """Tree structure for AWS data."""

    def __init__(self, name: str, ou_id: str, iterations: list[Iteration]) -> None:
        """Initialize AWSTree object."""
        self.name = name
        self.ou_id = ou_id
        self.iterations = iterations

    def __repr__(self) -> str:
        """Overload to repr function for AWSTree object."""
        return f"AWSTree('{self.name}', '{self.ou_id}', {self.iterations})"

    def __eq__(self, other: AWSTree) -> bool:
        """Overload equals operator for AWSTree objects."""
        if not isinstance(other, AWSTree):
            raise TypeError("Must compare to object of type AWSTree")
        return self.name == other.name and self.ou_id == other.ou_id and self.iterations == other.iterations

    def awstree_to_syncdata_list(self) -> list[SyncData]:
        """Convert AWSTree to list of SyncData elements."""
        return [member for iteration in self.iterations for member in iteration.members]
