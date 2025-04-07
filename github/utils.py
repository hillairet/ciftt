"""
Utility functions for GitHub operations.
"""
from typing import Optional, Tuple
import re


def parse_repo(repo: str) -> Tuple[str, str]:
    """Parse the repository string into owner and repo name."""
    try:
        owner, repo_name = repo.split("/")
        return owner, repo_name
    except ValueError:
        raise ValueError("Repository must be in format 'owner/repo'")


def extract_issue_number(url: str) -> Optional[int]:
    """Extract the issue number from a GitHub issue URL."""
    if not url or not isinstance(url, str):
        return None

    # Match patterns like https://github.com/owner/repo/issues/123
    match = re.search(r"/issues/(\d+)$", url)
    if match:
        return int(match.group(1))
    return None
