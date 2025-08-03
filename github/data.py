from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BaseIssue(BaseModel):
    """
    Base class for GitHub issues with common fields.
    """

    body: Optional[str] = Field(default=None, alias=["description", "Description"])
    labels: Optional[List[str]] = Field(default=None, alias="Labels")
    assignees: Optional[List[str]] = Field(default=None, alias="Assignees")

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

    title: str = Field(alias="Title")


class UpdatedIssue(BaseIssue):
    """
    Represents updates to an existing GitHub issue.
    """

    title: Optional[str] = Field(default=None, alias="Title")
    state: Optional[Literal["open", "closed"]] = Field(default=None, alias="State")
    state_reason: Optional[Literal["completed", "not_planned", "reopened"]] = None
    issue_number: int
    project_fields: Optional[Dict[str, str]] = None
    url: Optional[str] = Field(default=None, alias="URL")
