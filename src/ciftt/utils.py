"""
Utility functions for CIFTT.
"""

import codecs
import re
from dataclasses import dataclass
from typing import Literal, Optional, Tuple


@dataclass(frozen=True)
class IssueUrlParts:
    owner: str
    repo: str
    number: int
    kind: Literal["issue", "pull"]


def parse_repo(repo: str) -> Tuple[str, str]:
    """Parse the repository string into owner and repo name."""
    try:
        owner, repo_name = repo.split("/")
        return owner, repo_name
    except ValueError as e:
        raise ValueError("Repository must be in format 'owner/repo'") from e


def extract_issue_number(url: str) -> Optional[int]:
    """Extract the issue number from a GitHub issue URL."""
    if not url or not isinstance(url, str):
        return None

    # Match patterns like https://github.com/owner/repo/issues/123
    match = re.search(r"/issues/(\d+)$", url)
    if match:
        return int(match.group(1))
    return None


def parse_github_issue_or_pull_url(url: str) -> IssueUrlParts:
    pattern = r"^https://github\.com/([^/]+)/([^/]+)/(issues|pull)/(\d+)$"
    match = re.match(pattern, url or "")
    if not match:
        raise ValueError(f"Invalid GitHub issue or pull request URL: {url}")

    kind: Literal["issue", "pull"] = "issue" if match.group(3) == "issues" else "pull"
    return IssueUrlParts(
        owner=match.group(1),
        repo=match.group(2),
        number=int(match.group(4)),
        kind=kind,
    )


def is_github_pull_request_url(url: str) -> bool:
    try:
        return parse_github_issue_or_pull_url(url).kind == "pull"
    except ValueError:
        return False


def safe_decode(x):
    """
    Safely decode Unicode escape sequences in a string.

    Args:
        x: String that may contain Unicode escape sequences

    Returns:
        Decoded string, or original string if decoding fails
    """
    if isinstance(x, str):
        try:
            return codecs.decode(x, "unicode_escape")
        except UnicodeDecodeError:
            # If decoding fails, return the original string
            return x
    return x


def parse_issue_numbers(issues_str: str) -> list:
    """
    Parse a string of comma-separated issue numbers and ranges into a list of integers.

    Args:
        issues_str: String in format like '1,3-5,8'

    Returns:
        List of integers representing issue numbers

    Raises:
        ValueError: If the input string contains invalid issue numbers or ranges
    """
    if not issues_str:
        return None

    issue_numbers = []
    parts = issues_str.split(",")

    for part in parts:
        part = part.strip()
        if "-" in part:
            # Handle range (e.g., "123-126")
            try:
                start, end = map(int, part.split("-"))
                issue_numbers.extend(range(start, end + 1))
            except ValueError as e:
                raise ValueError(f"Invalid issue range: {part}") from e
        else:
            # Handle single issue number
            try:
                issue_numbers.append(int(part))
            except ValueError as e:
                raise ValueError(f"Invalid issue number: {part}") from e

    return issue_numbers


def parse_github_project_identifier(project_identifier: str) -> Tuple[str, str]:
    """
    Parse various GitHub project identifier formats to extract owner and project number.

    Supported formats:
    - Full URLs: https://github.com/users/owner/projects/123
    - Full URLs: https://github.com/orgs/orgname/projects/456
    - Short format: owner/projects/123
    - Shortest format: owner/123

    Args:
        project_identifier: Project identifier in one of the supported formats

    Returns:
        Tuple of (owner/org, project_number)
    """
    # Pattern 1: Full GitHub URLs
    url_pattern = r"https://github\.com/(?:users|orgs)/([^/]+)/projects/(\d+)"
    match = re.match(url_pattern, project_identifier)
    if match:
        return match.group(1), match.group(2)

    # Pattern 2: Short format - owner/projects/123
    short_pattern = r"^([^/]+)/projects/(\d+)$"
    match = re.match(short_pattern, project_identifier)
    if match:
        return match.group(1), match.group(2)

    # Pattern 3: Shortest format - owner/123
    shortest_pattern = r"^([^/]+)/(\d+)$"
    match = re.match(shortest_pattern, project_identifier)
    if match:
        return match.group(1), match.group(2)

    raise ValueError(
        f"Invalid project identifier format: {project_identifier}\n"
        f"Supported formats:\n"
        f"  - https://github.com/users/owner/projects/123\n"
        f"  - https://github.com/orgs/owner/projects/123\n"
        f"  - owner/projects/123\n"
        f"  - owner/123"
    )


def extract_repo_from_issue_url(issue_url: str) -> Tuple[str, str]:
    """
    Extract repository owner and name from a GitHub issue URL.

    Args:
        issue_url: GitHub issue URL like https://github.com/owner/repo/issues/123

    Returns:
        Tuple of (owner, repo_name)
    """
    # Match pattern: https://github.com/owner/repo/issues/123
    pattern = r"https://github\.com/([^/]+)/([^/]+)/issues/\d+"

    match = re.match(pattern, issue_url)
    if not match:
        raise ValueError(f"Invalid GitHub issue URL format: {issue_url}")

    owner = match.group(1)
    repo_name = match.group(2)

    return owner, repo_name
