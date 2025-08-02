import typer

from transform import transform_csv_to_updated_issues

from .csv_data import load_and_validate_csv
from .dry_run import perform_dry_run
from .github import (
    init_github_client,
    validate_repo,
    validate_repository_access,
    validate_token_scopes,
)
from .issues import update_issues_in_github


def update_issues(
    csv_file: str = typer.Argument(
        ..., help="Path to the CSV file containing issue data"
    ),
    repo: str = typer.Argument(..., help="GitHub repository in format 'owner/repo'"),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-d", help="Print actions without executing them"
    ),
):
    """
    Update existing GitHub issues from a CSV file.
    """
    typer.echo(f"🔍 Reading CSV file: {csv_file}")

    csv_data = load_and_validate_csv(csv_file)

    owner, repo_name = validate_repo(repo)

    typer.echo(f"🎯 Target repository: {owner}/{repo_name}")

    if dry_run:
        perform_dry_run(csv_data)
        return

    github_client = init_github_client()

    validate_token_scopes(github_client, ["repo"])
    validate_repository_access(github_client, owner, repo_name)

    issues = transform_csv_to_updated_issues(csv_data.data)

    update_issues_in_github(github_client, owner, repo_name, issues)
