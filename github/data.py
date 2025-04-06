from typing import List, Optional
from pydantic import BaseModel


class NewIssue(BaseModel):
    """
    Represents a new GitHub issue to be created.
    """
    title: str
    body: Optional[str] = None
    labels: Optional[List[str]] = None
    assignees: Optional[List[str]] = None


class UpdatedIssue(BaseModel):
    """
    Represents updates to an existing GitHub issue.
    """
    title: Optional[str] = None
    body: Optional[str] = None
    state: Optional[str] = None
    labels: Optional[List[str]] = None
    assignees: Optional[List[str]] = None
