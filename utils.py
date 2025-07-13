"""
Utility functions for CIFTT.
"""
from typing import Optional, Tuple
import re
import codecs


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
    parts = issues_str.split(',')
    
    for part in parts:
        part = part.strip()
        if '-' in part:
            # Handle range (e.g., "123-126")
            try:
                start, end = map(int, part.split('-'))
                issue_numbers.extend(range(start, end + 1))
            except ValueError:
                raise ValueError(f"Invalid issue range: {part}")
        else:
            # Handle single issue number
            try:
                issue_numbers.append(int(part))
            except ValueError:
                raise ValueError(f"Invalid issue number: {part}")
            
    return issue_numbers
