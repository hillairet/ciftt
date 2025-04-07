"""
Utility functions for GitHub operations.
"""
from typing import Tuple


def parse_repo(repo: str) -> Tuple[str, str]:
    """Parse the repository string into owner and repo name."""
    try:
        owner, repo_name = repo.split("/")
        return owner, repo_name
    except ValueError:
        raise ValueError("Repository must be in format 'owner/repo'")
