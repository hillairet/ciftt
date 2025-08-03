from typing import Set, Tuple

import typer

from transform import transform_csv_to_updated_issues
from utils import extract_repo_from_issue_url, parse_github_project_identifier

from .csv_data import load_and_validate_csv
from .dry_run import perform_dry_run
from .github import (
    init_github_client,
    validate_repository_access,
    validate_token_scopes,
)
from .issues import update_issues_in_github


def validate_project_identifier(project_identifier: str) -> Tuple[str, str]:
    """
    Validate and parse a GitHub project identifier.

    Args:
        project_identifier: GitHub project identifier in various formats

    Returns:
        Tuple of (owner, project_number)

    Raises:
        typer.Exit: If project identifier is invalid
    """
    try:
        owner, project_number = parse_github_project_identifier(project_identifier)
        return owner, project_number
    except ValueError as e:
        typer.echo(f"❌ Error: {e}")
        raise typer.Exit(code=1)


def extract_repositories_from_csv(csv_data) -> Set[Tuple[str, str]]:
    """
    Extract unique repositories from issue URLs in CSV data.

    Args:
        csv_data: CSVData instance

    Returns:
        Set of (owner, repo_name) tuples
    """
    repositories = set()

    for _, row in csv_data.data.iterrows():
        issue_url = row.get("URL")
        if issue_url:
            try:
                owner, repo_name = extract_repo_from_issue_url(issue_url)
                repositories.add((owner, repo_name))
            except ValueError:
                # Skip invalid URLs
                continue

    return repositories


def update_issues(
    csv_file: str = typer.Argument(
        ..., help="Path to the CSV file containing issue data"
    ),
    project: str = typer.Argument(
        ..., help="GitHub project (formats: owner/123, owner/projects/123, or full URL)"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-d", help="Print actions without executing them"
    ),
):
    """
    Update existing GitHub issues and their project fields from a CSV file.
    """
    typer.echo(f"🔍 Reading CSV file: {csv_file}")

    csv_data = load_and_validate_csv(csv_file)

    # Show project field detection info
    if csv_data.has_project_fields():
        typer.echo(
            f"📊 Detected project fields: {', '.join(csv_data.project_field_columns)}"
        )
    else:
        typer.echo("📋 No project fields detected - updating issues only")

    # Parse and validate project identifier
    project_owner, project_number = validate_project_identifier(project)
    typer.echo(f"🎯 Target project: {project_owner}/projects/{project_number}")

    # Extract repositories from issue URLs
    repositories = extract_repositories_from_csv(csv_data)
    if repositories:
        repo_list = [f"{owner}/{repo}" for owner, repo in repositories]
        typer.echo(f"📂 Repositories found in CSV: {', '.join(repo_list)}")
    else:
        typer.echo("❌ No valid issue URLs found in CSV")
        raise typer.Exit(code=1)

    if dry_run:
        perform_dry_run(csv_data)
        return

    github_client = init_github_client()

    validate_token_scopes(github_client, ["repo", "project"])

    # Validate that the project exists and is accessible
    try:
        project_info = github_client.validate_project_exists(
            project_owner, project_number
        )
        typer.echo(
            f"✅ Project validated: {project_info['title']} ({project_info['type']})"
        )
    except ValueError as e:
        typer.echo(f"❌ Project validation failed: {e}")
        raise typer.Exit(code=1)

    # Validate project fields before processing issues
    if csv_data.has_project_fields():
        try:
            field_definitions = github_client.get_project_field_definitions(
                project_owner, project_number
            )

            # Check if all CSV project fields exist in the project
            invalid_fields = []
            valid_fields = []

            for csv_field in csv_data.project_field_columns:
                if csv_field in field_definitions:
                    valid_fields.append(csv_field)
                else:
                    invalid_fields.append(csv_field)

            if invalid_fields:
                typer.echo(
                    f"❌ Invalid project fields found: {', '.join(invalid_fields)}"
                )
                available_fields = list(field_definitions.keys())
                typer.echo(
                    f"📋 Available project fields: {', '.join(available_fields)}"
                )
                raise typer.Exit(code=1)
            else:
                typer.echo(f"✅ Project fields validated: {', '.join(valid_fields)}")

        except ValueError as e:
            typer.echo(f"❌ Project field validation failed: {e}")
            raise typer.Exit(code=1)

    # Validate access to all repositories found in CSV
    for owner, repo_name in repositories:
        validate_repository_access(github_client, owner, repo_name)

    issues = transform_csv_to_updated_issues(csv_data)

    update_issues_in_github(github_client, issues, project_number)
