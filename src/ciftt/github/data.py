from typing import Any, Dict, List, Literal, Optional

from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from ciftt.utils import extract_issue_number, safe_decode


class BaseIssue(BaseModel):
    """
    Base class for GitHub issues with common fields.
    """

    body: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("body", "description", "Description"),
    )
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

    @classmethod
    def _decode_escape_sequences(cls, v: Any) -> Optional[str]:
        """Decode escape sequences like \\n, \\t, \\r in string values."""
        if v is None:
            return None
        return safe_decode(v)

    process_body = field_validator("body", mode="before")(_decode_escape_sequences)
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

    @field_validator("title", mode="before")
    @classmethod
    def validate_title(cls, v: Any) -> str:
        """Validate and normalize title field."""
        if v is None:
            raise ValueError("Title is required for new issues")

        if isinstance(v, str):
            v = v.strip()

        if not v or (isinstance(v, str) and not v.strip()):
            raise ValueError("Title cannot be empty")

        return v


class UpdatedIssue(BaseIssue):
    """
    Represents updates to an existing GitHub issue.
    """

    title: Optional[str] = Field(default=None, alias="Title")
    state: Optional[Literal["open", "closed"]] = Field(default=None, alias="State")
    state_reason: Optional[
        Literal["completed", "not_planned", "duplicate", "reopened"]
    ] = Field(default=None, alias="StateReason")
    issue_number: Optional[int] = None
    project_fields: Optional[Dict[str, str]] = None
    url: Optional[str] = Field(default=None, alias="URL")

    @model_validator(mode="before")
    @classmethod
    def extract_issue_number_from_url(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Extract issue_number from URL if not explicitly provided."""
        if not isinstance(values, dict):
            return values

        if "issue_number" in values and values.get("issue_number") is not None:
            return values

        url = values.get("url") or values.get("URL")
        if not url:
            raise ValueError(
                "Either issue_number or URL with issue number is required for updating issues"
            )

        issue_num = extract_issue_number(url)
        if not issue_num:
            raise ValueError(f"Could not extract issue number from URL: {url}")

        values["issue_number"] = issue_num
        return values

    @field_validator("issue_number", mode="after")
    @classmethod
    def validate_issue_number(cls, v: Optional[int]) -> int:
        """Ensure issue_number is present after extraction."""
        if v is None:
            raise ValueError("issue_number is required for updating issues")
        return v


class ProjectInfo(BaseModel):
    """
    Represents GitHub Project v2 information.
    """

    id: str
    title: str
    number: int
    url: str
    owner: str
    type: Literal["user", "organization"]


class TransferIssueInfo(BaseModel):
    id: str
    number: int
    url: str
    state: Literal["OPEN", "CLOSED"]
    parent_number: Optional[int] = None


class TransferredIssue(BaseModel):
    id: str
    number: int
    url: str


class ProjectFieldUpdateResult(BaseModel):
    """
    Represents the result of updating project fields for an issue.
    """

    updated_fields: Dict[str, str] = Field(default_factory=dict)
    errors: Dict[str, str] = Field(default_factory=dict)


class ProjectFieldValue(BaseModel):
    """
    Base class for project field values. Different field types have different value structures.
    """

    pass


class TextFieldValue(ProjectFieldValue):
    """Text field value for GitHub Projects v2."""

    text: str


class NumberFieldValue(ProjectFieldValue):
    """Number field value for GitHub Projects v2."""

    number: float


class DateFieldValue(ProjectFieldValue):
    """Date field value for GitHub Projects v2."""

    date: str


class SingleSelectFieldValue(ProjectFieldValue):
    """Single select field value for GitHub Projects v2."""

    singleSelectOptionId: str


class IterationFieldValue(ProjectFieldValue):
    """Iteration field value for GitHub Projects v2."""

    iterationId: str


class IssueNodeInfo(BaseModel):
    """
    Represents basic GitHub issue information with node ID.
    """

    id: str
    number: int
    title: str
    url: str


class ProjectItemResult(BaseModel):
    """
    Represents the result of adding an issue to a project.
    """

    item_id: str
    issue_number: int
    issue_url: str
