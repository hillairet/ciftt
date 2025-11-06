import typer

from ciftt.transform import transform_csv_to_new_issues

from .common import load_csv_for_command, setup_github_client_for_command
from .dry_run import perform_dry_run
from .github import validate_repo
from .issues import create_issues_in_github


def create_issues(
    csv_file: str = typer.Argument(
        ..., help="Path to the CSV file containing issue data"
    ),
    repo: str = typer.Argument(..., help="GitHub repository in format 'owner/repo'"),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-d", help="Print actions without executing them"
    ),
):
    """
    Create new GitHub issues from a CSV file.
    """
    csv_data = load_csv_for_command(csv_file)

    owner, repo_name = validate_repo(repo)
    typer.echo(f"🎯 Target repository: {owner}/{repo_name}")

    if dry_run:
        perform_dry_run(csv_data)
        return

    github_client = setup_github_client_for_command(
        required_scopes=["repo"], repositories=[(owner, repo_name)]
    )

    issues = transform_csv_to_new_issues(csv_data.data)

    create_issues_in_github(github_client, owner, repo_name, issues)
