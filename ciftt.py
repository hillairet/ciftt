#!/usr/bin/env python3
"""
CIFTT - CSV Input for Feature Triage and Tracking
A tool to create or update GitHub issues from CSV input.
"""
from typing import Optional, Tuple
import re

import typer

from csv_data import CSVData
from github import GitHubClient, NewIssue, UpdatedIssue
from settings import Settings

app = typer.Typer(help="CIFTT - CSV Input for Feature Triage and Tracking")
settings = Settings()


def parse_repo(repo: str) -> Tuple[str, str]:
    """Parse the repository string into owner and repo name."""
    try:
        owner, repo_name = repo.split("/")
        return owner, repo_name
    except ValueError:
        raise typer.BadParameter("Repository must be in format 'owner/repo'")


def extract_issue_number(url: str) -> Optional[int]:
    """Extract the issue number from a GitHub issue URL."""
    if not url or not isinstance(url, str):
        return None
    
    # Match patterns like https://github.com/owner/repo/issues/123
    match = re.search(r'/issues/(\d+)$', url)
    if match:
        return int(match.group(1))
    return None


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
            issue_number = extract_issue_number(row.get('url'))
            if issue_number:
                typer.echo(f"Would update issue #{issue_number}: {row['title']}")
            else:
                typer.echo(f"Would create issue: {row['title']}")
        return

    # Initialize GitHub client
    try:
        github_client = GitHubClient(api_key=settings.github_token.get_secret_value())
        typer.echo("✅ Connected to GitHub API")
    except Exception as e:
        typer.echo(f"❌ Failed to initialize GitHub client: {e}")
        raise typer.Exit(code=1)

    # Process issues (create or update)
    created_issues = []
    updated_issues = []
    
    for index, row in csv_data.data.iterrows():
        try:
            issue_number = extract_issue_number(row.get('url'))
            
            # Common fields for both new and updated issues
            title = row["title"]
            body = row.get("description", row.get("body", None))
            labels = (
                row.get("labels", "").split(",")
                if row.get("labels") and isinstance(row.get("labels"), str)
                else None
            )
            assignees = (
                row.get("assignees", "").split(",")
                if row.get("assignees") and isinstance(row.get("assignees"), str)
                else None
            )
            
            if issue_number:
                # Update existing issue
                issue_update = UpdatedIssue(
                    title=title,
                    body=body,
                    labels=labels,
                    assignees=assignees,
                )
                response = github_client.update_issue(owner, repo_name, issue_number, issue_update)
                updated_issues.append(response)
                typer.echo(f"✅ Updated issue #{response['number']}: {response['title']}")
            else:
                # Create new issue
                new_issue = NewIssue(
                    title=title,
                    body=body,
                    labels=labels,
                    assignees=assignees,
                )
                response = github_client.create_issue(owner, repo_name, new_issue)
                created_issues.append(response)
                typer.echo(f"✅ Created issue #{response['number']}: {response['title']}")
                
        except Exception as e:
            typer.echo(f"❌ Failed to process issue '{row['title']}': {e}")

    typer.echo(f"🎉 Created {len(created_issues)} issues and updated {len(updated_issues)} issues successfully")


if __name__ == "__main__":
    app()
