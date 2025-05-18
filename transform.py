"""
Transform CSV data into GitHub issue instances.
"""

from typing import List, Union

import pandas as pd

from github import BaseIssue, NewIssue, UpdatedIssue
from utils import extract_issue_number


def transform_row_to_issue(row: pd.Series) -> BaseIssue:
    """
    Transform a CSV row into a GitHub issue instance.

    Args:
        row: A pandas Series representing a row from the CSV data

    Returns:
        A BaseIssue instance (either NewIssue or UpdatedIssue)
    """
    # Convert pandas Series to dict, removing NaN values
    row_dict = row.dropna().to_dict()

    # Extract issue number from URL if present
    issue_number = extract_issue_number(row_dict.get("url"))

    # Remove URL as it's not a field in the model
    if "url" in row_dict:
        row_dict.pop("url")

    if issue_number:
        # Update existing issue
        row_dict["issue_number"] = issue_number

        try:
            return UpdatedIssue.model_validate(row_dict)
        except Exception as e:
            raise ValueError(f"Invalid update issue data: {e}")
    else:
        # Create new issue - title is required
        if "title" not in row_dict or row_dict.get("title") == "":
            raise ValueError("Title is required for new issues")

        try:
            return NewIssue.model_validate(row_dict)
        except Exception as e:
            raise ValueError(f"Invalid new issue data: {e}")


def transform_csv_to_issues(data: pd.DataFrame) -> List[BaseIssue]:
    """
    Transform CSV data into a list of GitHub issue instances.

    Args:
        data: A pandas DataFrame containing the CSV data

    Returns:
        A list of BaseIssue instances (either NewIssue or UpdatedIssue)
    """
    issues = []

    for _, row in data.iterrows():
        try:
            issue = transform_row_to_issue(row)
            issues.append(issue)
        except Exception as e:
            # Log the error and continue with the next row
            print(f"Error transforming row: {e}")
            continue

    return issues
