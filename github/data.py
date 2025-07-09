from typing import Any, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BaseIssue(BaseModel):
    """
    Base class for GitHub issues with common fields.
    """

    body: Optional[str] = Field(default=None, alias="description")
    labels: Optional[List[str]] = None
    assignees: Optional[List[str]] = None

    model_config = ConfigDict(
        populate_by_name=True  # Allow both alias and field name to be used
    )

    @classmethod
    def _process_comma_separated_list(cls, v: Any) -> Optional[List[str]]:
        """Process a value from string to list by splitting on commas."""
        if not v:
            return None

        # If it's already a list, return it
        if isinstance(v, list):
            return v

        # If it's a string, split by comma and strip whitespace
        if isinstance(v, str):
            # Filter out empty strings after splitting
            items = [item.strip() for item in v.split(",") if item.strip()]
            return items if items else None

        return v

    # Use the same processing function for both fields
    process_assignees = field_validator("assignees", mode="before")(
        _process_comma_separated_list
    )
    process_labels = field_validator("labels", mode="before")(
        _process_comma_separated_list
    )


class NewIssue(BaseIssue):
    """
    Represents a new GitHub issue to be created.
    """

    title: str


class UpdatedIssue(BaseIssue):
    """
    Represents updates to an existing GitHub issue.
    """

    title: Optional[str] = None
    state: Optional[Literal["open", "closed"]] = None
    state_reason: Optional[Literal["completed", "not_planned", "reopened"]] = None
    issue_number: int
