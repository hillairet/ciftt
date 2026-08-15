"""
Transform CSV data into GitHub issue instances.
"""

from typing import List

import pandas as pd

from ciftt.github import NewIssue, UpdatedIssue


def transform_csv_to_new_issues(data: pd.DataFrame) -> List[NewIssue]:
    """
    Transform CSV data into a list of new GitHub issue instances.

    Args:
        data: A pandas DataFrame containing the CSV data

    Returns:
        A list of NewIssue instances
    """
    issues = []

    for _, row in data.iterrows():
        try:
            # Convert pandas Series to dict, removing NaN values
            row_dict = row.dropna().to_dict()

            # Remove URL as it's not a field in the model and shouldn't be present for new issues
            if "URL" in row_dict:
                row_dict.pop("URL")

            issue = NewIssue.model_validate(row_dict)
            issues.append(issue)
        except Exception as e:
            # Log the error and continue with the next row
            print(f"Error transforming row to new issue: {e}")
            continue

    return issues


def transform_csv_to_updated_issues(csv_data) -> List[UpdatedIssue]:
    """
    Transform CSV data into a list of updated GitHub issue instances.

    Args:
        csv_data: CSVData instance containing the CSV data

    Returns:
        A list of UpdatedIssue instances
    """
    issues = []

    for index, row in csv_data.data.iterrows():
        try:
            # Convert pandas Series to dict, removing NaN values
            row_dict = row.dropna().to_dict()

            # Extract project fields from the CSV data
            project_fields = csv_data.get_project_field_data(index)
            if project_fields:
                row_dict["project_fields"] = project_fields

            # Remove project field columns from the main row_dict to avoid conflicts
            for field_name in csv_data.project_field_columns:
                row_dict.pop(field_name, None)

            issue = UpdatedIssue.model_validate(row_dict)
            issues.append(issue)
        except Exception as e:
            # Log the error and continue with the next row
            print(f"Error transforming row to updated issue: {e}")
            continue

    return issues


def transform_issues_to_dataframe(
    issues_data: List[dict],
    project_field_data: dict = None,
    field_names: List[str] = None,
) -> pd.DataFrame:
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
            "Title": issue["title"],
            "Description": description,
            "Labels": ",".join([label["name"] for label in issue["labels"]]),
            "Assignee": issue["assignee"]["login"] if issue["assignee"] else "",
            "StateReason": issue.get("state_reason") or "",
            "URL": issue["html_url"],
        }

        # Add project fields if available
        if project_field_data and field_names and issue["number"] in project_field_data:
            for field_name in field_names:
                row[field_name] = project_field_data[issue["number"]].get(
                    field_name, ""
                )

        rows.append(row)

    return pd.DataFrame(rows)
