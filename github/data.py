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
