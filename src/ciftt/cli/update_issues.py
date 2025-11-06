from typing import Set, Tuple

import typer

from ciftt.transform import transform_csv_to_updated_issues
from ciftt.utils import extract_repo_from_issue_url, parse_github_project_identifier

from .common import (
    handle_cli_error,
    load_csv_for_command,
    setup_github_client_for_command,
    validate_project_fields_for_csv,
)
from .dry_run import perform_dry_run
from .issues import update_issues_in_github


def _validate_project_identifier(project_identifier: str) -> Tuple[str, str]:
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


def _extract_repositories_from_csv(csv_data) -> Set[Tuple[str, str]]:
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
    project: str = typer.Option(
        None,
        "--project",
        "-p",
        help="GitHub project (formats: owner/123, owner/projects/123, or full URL). Required only if updating project fields.",
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-d", help="Print actions without executing them"
    ),
):
    """
    Update existing GitHub issues and optionally their project fields from a CSV file.
    """
    csv_data = load_csv_for_command(csv_file)

    # Show project field detection info and handle project requirement
    if csv_data.has_project_fields():
        typer.echo(
            f"📊 Detected project fields: {', '.join(csv_data.project_field_columns)}"
        )
        if not project:
            typer.echo(
                f"⚠️  Warning: Project fields detected but no project provided. "
                f"The following columns will be ignored: {', '.join(csv_data.project_field_columns)}"
            )
            typer.echo("💡 Tip: Use --project option to update project fields")
    else:
        typer.echo("📋 No project fields detected - updating issues only")

    # Parse and validate project identifier only if provided
    project_owner = None
    project_number = None
    if project:
        project_owner, project_number = _validate_project_identifier(project)
        typer.echo(f"🎯 Target project: {project_owner}/projects/{project_number}")

    # Extract repositories from issue URLs
    repositories = _extract_repositories_from_csv(csv_data)
    if repositories:
        repo_list = [f"{owner}/{repo}" for owner, repo in repositories]
        typer.echo(f"📂 Repositories found in CSV: {', '.join(repo_list)}")
    else:
        typer.echo("❌ No valid issue URLs found in CSV")
        raise typer.Exit(code=1)

    if dry_run:
        perform_dry_run(csv_data)
        return

    # Determine required scopes based on whether project operations are needed
    required_scopes = ["repo"]
    if project:
        required_scopes.append("project")

    github_client = setup_github_client_for_command(
        required_scopes=required_scopes, repositories=repositories
    )

    # Validate project and fields only if project is provided
    if project:
        # Validate that the project exists and is accessible
        try:
            project_info = github_client.validate_project_exists(
                project_owner, project_number
            )
            typer.echo(
                f"✅ Project validated: {project_info.title} ({project_info.type})"
            )
        except ValueError as e:
            handle_cli_error("Project validation", e)

        # Validate project fields before processing issues
        validate_project_fields_for_csv(
            csv_data, github_client, project_owner, project_number
        )

    # Repository access already validated by setup_github_client_for_command

    issues = transform_csv_to_updated_issues(csv_data)

    update_issues_in_github(github_client, issues, project_number)
