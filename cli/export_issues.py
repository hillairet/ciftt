import pandas as pd
import typer

from github import GitHubClient
from settings import Settings
from transform import transform_issues_to_dataframe
from utils import parse_issue_numbers

from .csv_data import save_df_to_csv
from .github import init_github_client, validate_repo
from .issues import fetch_issues_from_github, parse_provided_issue_numbers
from .project_fields import fetch_github_project_fields


def export_issues(
    repo: str = typer.Argument(..., help="GitHub repository in format 'owner/repo'"),
    output_file: str = typer.Argument(..., help="Path to save the CSV output file"),
    all_issues: bool = typer.Option(
        False, "--all", "-a", help="Export all issues, not just open ones"
    ),
    issues: str = typer.Option(
        None,
        "--issues",
        "-i",
        help="Comma-separated list of issue numbers or ranges (e.g., '1,3-5,8')",
    ),
    project_fields: str = typer.Option(
        None,
        "--fields",
        "-f",
        help="Comma-separated list of GitHub Project v2 fields to include in export",
    ),
):
    """
    Export GitHub issues to a CSV file that can be used for updates.
    """
    settings = Settings()

    typer.echo(f"🔍 Exporting issues from repository: {repo}")

    owner, repo_name = validate_repo(repo)

    github_client = init_github_client()

    issue_numbers = parse_provided_issue_numbers(issues)

    issues_data = fetch_issues_from_github(
        github_client, owner, repo_name, issue_numbers, all_issues
    )

    project_field_data, field_names = fetch_github_project_fields(
        github_client, owner, repo_name, issues_data, project_fields
    )

    df = transform_issues_to_dataframe(issues_data, project_field_data, field_names)

    save_df_to_csv(df, output_file)
