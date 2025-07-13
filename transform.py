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


def transform_issues_to_dataframe(issues_data: List[dict], project_field_data: dict = None, field_names: List[str] = None) -> pd.DataFrame:
    """
    Transform GitHub issues data into a pandas DataFrame for CSV export.

    Args:
        issues_data: List of GitHub issue dictionaries
        project_field_data: Optional dictionary of project field data by issue number
        field_names: Optional list of project field names to include

    Returns:
        A pandas DataFrame ready for CSV export
    """
    rows = []
    for issue in issues_data:
        # Replace newlines with \n in description to keep each issue on one line in CSV
        description = issue["body"] or ""
        description = description.replace("\r\n", "\\n").replace("\n", "\\n")

        row = {
            "title": issue["title"],
            "description": description,
            "labels": ",".join([label["name"] for label in issue["labels"]]),
            "assignee": issue["assignee"]["login"] if issue["assignee"] else "",
            "url": issue["html_url"],
        }

        # Add project fields if available
        if project_field_data and field_names and issue["number"] in project_field_data:
            for field_name in field_names:
                row[field_name] = project_field_data[issue["number"]].get(
                    field_name, ""
                )

        rows.append(row)

    return pd.DataFrame(rows)
