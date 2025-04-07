"""
Transform CSV data into GitHub issue instances.
"""

from typing import List, Union

import pandas as pd

from github import BaseIssue, NewIssue, UpdatedIssue, extract_issue_number


def transform_row_to_issue(row: pd.Series) -> BaseIssue:
    """
    Transform a CSV row into a GitHub issue instance.

    Args:
        row: A pandas Series representing a row from the CSV data

    Returns:
        A BaseIssue instance (either NewIssue or UpdatedIssue)
    """
    # Extract issue number from URL if present
    issue_number = extract_issue_number(row.get("url"))

    # Common fields for both new and updated issues
    title = row["title"]
    body = row.get("description", row.get("body", None))

    # Process labels if present
    labels = None
    if row.get("labels") and isinstance(row.get("labels"), str):
        # Filter out empty strings after splitting
        labels = [
            label.strip() for label in row.get("labels", "").split(",") if label.strip()
        ]
        if not labels:  # If all labels were empty strings
            labels = None

    # Process assignees if present
    assignees = None
    if row.get("assignees") and isinstance(row.get("assignees"), str):
        # Filter out empty strings after splitting
        assignees = [
            assignee.strip()
            for assignee in row.get("assignees", "").split(",")
            if assignee.strip()
        ]
        if not assignees:  # If all assignees were empty strings
            assignees = None

    # Create the appropriate issue type based on whether we're updating or creating
    if issue_number:
        # Update existing issue
        return UpdatedIssue(
            title=title,
            body=body,
            labels=labels,
            assignees=assignees,
            state=row.get("state"),
            state_reason=row.get("state_reason"),
            issue_number=issue_number,
        )
    else:
        # Create new issue
        return NewIssue(
            title=title,
            body=body,
            labels=labels,
            assignees=assignees,
        )


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
