#!/usr/bin/env python3
"""
CIFTT - CSV Input for Feature Triage and Tracking
A tool to create or update GitHub issues from CSV input.
"""
from typing import Optional, Tuple

import typer

from csv_data import CSVData
from github.client import GitHubClient
from github.data import NewIssue
from settings import Settings

app = typer.Typer(help="CIFTT - CSV Input for Feature Triage and Tracking")
settings = Settings()


def parse_repo(repo: str) -> Tuple[str, str]:
    """Parse the repository string into owner and repo name."""
    try:
        owner, repo_name = repo.split('/')
        return owner, repo_name
    except ValueError:
        raise typer.BadParameter("Repository must be in format 'owner/repo'")


@app.command()
def main(
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
    typer.echo(f"🔍 Reading CSV file: {csv_file}")

    try:
        # Load and validate the CSV data
        csv_data = CSVData(csv_file)
        typer.echo(f"✅ Successfully loaded CSV with {len(csv_data.data)} rows")
    except Exception as e:
        typer.echo(f"❌ Error: {e}")
        raise typer.Exit(code=1)

    # Parse the repository string
    owner, repo_name = parse_repo(repo)
    typer.echo(f"🎯 Target repository: {owner}/{repo_name}")

    if dry_run:
        typer.echo("🧪 DRY RUN MODE: No changes will be made on GitHub")
        for index, row in csv_data.data.iterrows():
            typer.echo(f"Would create issue: {row['title']}")
        return

    # Initialize GitHub client
    try:
        github_client = GitHubClient(api_key=settings.github_token)
        typer.echo("✅ Connected to GitHub API")
    except Exception as e:
        typer.echo(f"❌ Failed to initialize GitHub client: {e}")
        raise typer.Exit(code=1)

    # Create issues
    created_issues = []
    for index, row in csv_data.data.iterrows():
        try:
            # Create a NewIssue object from the row data
            issue = NewIssue(
                title=row['title'],
                body=row.get('body', None),
                labels=row.get('labels', "").split(",") if row.get('labels') else None,
                assignees=row.get('assignees', "").split(",") if row.get('assignees') else None
            )
            
            # Create the issue on GitHub
            if not dry_run:
                response = github_client.create_issue(owner, repo_name, issue)
                created_issues.append(response)
                typer.echo(f"✅ Created issue #{response['number']}: {response['title']}")
        except Exception as e:
            typer.echo(f"❌ Failed to create issue '{row['title']}': {e}")
    
    typer.echo(f"🎉 Created {len(created_issues)} issues successfully")


if __name__ == "__main__":
    app()
