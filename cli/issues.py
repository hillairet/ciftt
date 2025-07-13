from typing import List, Tuple

import typer

from github import GitHubClient, NewIssue, UpdatedIssue
from utils import parse_issue_numbers


def parse_provided_issue_numbers(issues: str) -> list:
    """
    Parse issue numbers from provided string.

    Args:
        issues: Comma-separated list of issue numbers or ranges, or empty

    Returns:
        List of issue numbers, or None if no issues provided

    Raises:
        typer.Exit: If issue numbers parsing fails
    """
    if not issues:
        return []

    try:
        issue_numbers = parse_issue_numbers(issues)
        typer.echo(f"🔢 Exporting specific issues: {issue_numbers}")
        return issue_numbers
    except ValueError as e:
        typer.echo(f"❌ Error parsing issue numbers: {e}")
        raise typer.Exit(code=1)


def fetch_issues_from_github(
    github_client: GitHubClient,
    owner: str,
    repo_name: str,
    issue_numbers: list,
    all_issues: bool,
) -> list:
    """
    Fetch issues from GitHub based on provided parameters.

    Args:
        github_client: GitHub client instance
        owner: Repository owner
        repo_name: Repository name
        issue_numbers: List of specific issue numbers to fetch, or empty list
        all_issues: Whether to fetch all issues or just open ones

    Returns:
        List of issue data

    Raises:
        typer.Exit: If fetching issues fails
    """
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

    if not issues_data:
        typer.echo("⚠️ No issues found to export")
        raise typer.Exit(code=0)

    return issues_data


def create_or_update_issues(
    github_client: GitHubClient,
    owner: str,
    repo_name: str,
    issues: List[NewIssue | UpdatedIssue],
) -> Tuple[List[dict], List[dict]]:
    """
    Process a list of issues by creating new ones or updating existing ones.

    Args:
        github_client: The GitHub client instance
        owner: Repository owner
        repo_name: Repository name
        issues: List of issue instances to process

    Returns:
        Tuple of (created_issues, updated_issues) lists
    """
    created_issues = []
    updated_issues = []

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

    return created_issues, updated_issues
