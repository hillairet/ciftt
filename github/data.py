from typing import List, Literal, Optional

from pydantic import BaseModel


class BaseIssue(BaseModel):
    """
    Base class for GitHub issues with common fields.
    """
    body: Optional[str] = None
    labels: Optional[List[str]] = None
    assignees: Optional[List[str]] = None


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
