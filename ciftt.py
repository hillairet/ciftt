#!/usr/bin/env python3
"""
CIFTT - CSV Input for Feature Triage and Tracking
A tool to create or update GitHub issues from CSV input.
"""
import typer

from csv_data import CSVData
from github import (
    GitHubClient,
    NewIssue,
    UpdatedIssue,
)
from settings import Settings
from utils import extract_issue_number, parse_repo

app = typer.Typer(help="CIFTT - CSV Input for Feature Triage and Tracking")
settings = Settings()


@app.command()
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
    typer.echo(f"🔍 Reading CSV file: {csv_file}")

    try:
        # Load and validate the CSV data
        csv_data = CSVData(csv_file)
        typer.echo(f"💾 Successfully loaded CSV with {len(csv_data.data)} rows")
    except Exception as e:
        typer.echo(f"❌ Error: {e}")
        raise typer.Exit(code=1)

    try:
        # Parse the repository string
        owner, repo_name = parse_repo(repo)
    except ValueError as e:
        typer.echo(f"❌ Error: {e}")
        raise typer.Exit(code=1)
    typer.echo(f"🎯 Target repository: {owner}/{repo_name}")

    if dry_run:
        typer.echo("🧪 DRY RUN MODE: No changes will be made on GitHub")
        for index, row in csv_data.data.iterrows():
            issue_number = extract_issue_number(row.get("url"))
            if issue_number:
                typer.echo(f"Would update issue #{issue_number}: {row['title']}")
            else:
                typer.echo(f"Would create issue: {row['title']}")
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

    from transform import transform_csv_to_issues

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


@app.command()
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
):
    """
    Export GitHub issues to a CSV file that can be used for updates.
    """
    typer.echo(f"🔍 Exporting issues from repository: {repo}")

    try:
        # Parse the repository string
        owner, repo_name = parse_repo(repo)
    except ValueError as e:
        typer.echo(f"❌ Error: {e}")
        raise typer.Exit(code=1)

    # Initialize GitHub client
    try:
        github_client = GitHubClient(api_key=settings.github_token.get_secret_value())
        typer.echo("🐙 Connected to GitHub API")
    except Exception as e:
        typer.echo(f"❌ Failed to initialize GitHub client: {e}")
        raise typer.Exit(code=1)

    # Parse issue numbers if provided
    issue_numbers = None
    if issues:
        try:
            from utils import parse_issue_numbers

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
    import pandas as pd

    if not issues_data:
        typer.echo("⚠️ No issues found to export")
        raise typer.Exit(code=0)

    # Create DataFrame from issues
    rows = []
    for issue in issues_data:
        # Replace newlines with \n in description to keep each issue on one line in CSV
        description = issue["body"] or ""
        description = description.replace("\r\n", "\\n").replace("\n", "\\n")
        
        row = {
            "title": issue["title"],
            "description": description,
            "labels": ",".join([label["name"] for label in issue["labels"]]),
            "assignee": issue["assignee"]["login"] if issue["assignee"] else "",
            "url": issue["html_url"],
        }
        rows.append(row)

    df = pd.DataFrame(rows)

    # Save to CSV
    try:
        df.to_csv(output_file, index=False)
        typer.echo(f"✅ Successfully exported {len(df)} issues to {output_file}")
    except Exception as e:
        typer.echo(f"❌ Failed to write CSV file: {e}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
