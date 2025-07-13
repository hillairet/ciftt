import pandas as pd
import typer

from github import GitHubClient
from settings import Settings
from transform import transform_issues_to_dataframe
from utils import parse_issue_numbers

from .github import init_github_client, validate_repo


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

    # Validate and parse repository
    owner, repo_name = validate_repo(repo)

    # Initialize GitHub client
    github_client = init_github_client()

    # Parse issue numbers if provided
    issue_numbers = None
    if issues:
        try:
            issue_numbers = parse_issue_numbers(issues)
            typer.echo(f"🔢 Exporting specific issues: {issue_numbers}")
        except ValueError as e:
            typer.echo(f"❌ Error parsing issue numbers: {e}")
            raise typer.Exit(code=1)

    # Fetch issues from GitHub
    try:
        if issue_numbers:
            issues_data = github_client.get_issues_by_numbers(
                owner, repo_name, issue_numbers
            )
        else:
            state = "all" if all_issues else "open"
            issues_data = github_client.get_all_issues(owner, repo_name, state=state)

        typer.echo(f"📋 Found {len(issues_data)} issues")
    except Exception as e:
        typer.echo(f"❌ Failed to fetch issues: {e}")
        raise typer.Exit(code=1)

    # Transform issues to CSV format
    if not issues_data:
        typer.echo("⚠️ No issues found to export")
        raise typer.Exit(code=0)

    # If project fields are requested, fetch them
    project_field_data = {}
    field_names = []
    if project_fields:
        field_names = [field.strip() for field in project_fields.split(",")]
        typer.echo(f"🔍 Fetching project fields: {', '.join(field_names)}")

        # Get issue numbers
        issue_numbers = [issue["number"] for issue in issues_data]

        try:
            project_field_data = github_client.get_project_fields_for_issues(
                owner, repo_name, issue_numbers, field_names
            )
            typer.echo(
                f"✅ Successfully fetched project fields for {len(project_field_data)} issues"
            )
        except Exception as e:
            typer.echo(f"⚠️ Warning: Failed to fetch project fields: {e}")

    # Create DataFrame from issues
    df = transform_issues_to_dataframe(issues_data, project_field_data, field_names)

    # Save to CSV
    try:
        df.to_csv(output_file, index=False)
        typer.echo(f"✅ Successfully exported {len(df)} issues to {output_file}")
    except Exception as e:
        typer.echo(f"❌ Failed to write CSV file: {e}")
        raise typer.Exit(code=1)
