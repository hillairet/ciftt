import typer

from github import GitHubClient, NewIssue, UpdatedIssue
from settings import Settings
from transform import transform_csv_to_issues

from .csv_data import load_and_validate_csv
from .dry_run import perform_dry_run
from .github import validate_repo


def import_issues(
    csv_file: str = typer.Argument(
        ..., help="Path to the CSV file containing issue data"
    ),
    repo: str = typer.Argument(..., help="GitHub repository in format 'owner/repo'"),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-d", help="Print actions without executing them"
    ),
):
    """
    Create or update GitHub issues from a CSV file.
    """
    settings = Settings()

    typer.echo(f"🔍 Reading CSV file: {csv_file}")

    # Load and validate the CSV data
    csv_data = load_and_validate_csv(csv_file)

    # Parse the repository string
    owner, repo_name = validate_repo(repo)

    typer.echo(f"🎯 Target repository: {owner}/{repo_name}")

    if dry_run:
        perform_dry_run(csv_data)
        return

    # Initialize GitHub client
    try:
        github_client = GitHubClient(api_key=settings.github_token.get_secret_value())
        typer.echo("🐙 Connected to GitHub API")
    except Exception as e:
        typer.echo(f"❌ Failed to initialize GitHub client: {e}")
        raise typer.Exit(code=1)

    # Process issues (create or update)
    created_issues = []
    updated_issues = []

    # Transform CSV data into issue instances
    issues = transform_csv_to_issues(csv_data.data)

    for issue in issues:
        try:
            if isinstance(issue, NewIssue):
                # Create new issue
                response = github_client.create_issue(owner, repo_name, issue)
                created_issues.append(response)
                typer.echo(
                    f"✅ Created issue #{response['number']}: {response['title']}"
                )
            elif isinstance(issue, UpdatedIssue):
                # Update existing issue
                response = github_client.update_issue(owner, repo_name, issue)
                updated_issues.append(response)
                typer.echo(
                    f"✅ Updated issue #{response['number']}: {response['title']}"
                )
        except Exception as e:
            issue_title = getattr(issue, "title", "Unknown")
            typer.echo(f"❌ Failed to process issue '{issue_title}': {e}")

    typer.echo(
        f"🎉 Created {len(created_issues)} issues and updated {len(updated_issues)} issues successfully"
    )
