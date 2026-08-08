from typing import Literal, Optional

import typer

from ciftt.github import GitHubClient, NewIssue, UpdatedIssue
from ciftt.utils import extract_repo_from_issue_url, parse_issue_numbers


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
        if issue_numbers is None:
            return []
        typer.echo(f"🔢 Exporting specific issues: {issue_numbers}")
        return issue_numbers
    except ValueError as e:
        typer.echo(f"❌ Error parsing issue numbers: {e}")
        raise typer.Exit(code=1) from e


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
            typer.echo(f"🔍 Fetching {len(issue_numbers)} specific issues...")

            def report_issue_progress(
                completed: int, total: int, issue_number: int
            ) -> None:
                if completed != 1 and completed % 25 != 0 and completed != total:
                    return

                typer.echo(
                    f"⏳ Fetched {completed}/{total} requested issues "
                    f"(latest: #{issue_number})"
                )

            issues_data = github_client.get_issues_by_numbers(
                owner,
                repo_name,
                issue_numbers,
                progress_callback=report_issue_progress,
            )
        else:
            state: Literal["open", "closed", "all"] = "all" if all_issues else "open"
            typer.echo(f"🔍 Fetching {state} issues from repository...")

            def report_page_progress(
                page: int, total_issues: int, page_issues: int
            ) -> None:
                page_label = "page" if page == 1 else "pages"
                typer.echo(
                    f"⏳ Fetched {total_issues} issues across {page} {page_label} "
                    f"(latest page: {page_issues})"
                )

            issues_data = github_client.get_all_issues(
                owner,
                repo_name,
                state=state,
                progress_callback=report_page_progress,
            )

        typer.echo(f"📋 Found {len(issues_data)} issues")
    except Exception as e:
        typer.echo(f"❌ Failed to fetch issues: {e}")
        raise typer.Exit(code=1) from e

    if not issues_data:
        typer.echo("⚠️ No issues found to export")
        raise typer.Exit(code=0)

    return issues_data


def create_issues_in_github(
    github_client: GitHubClient,
    owner: str,
    repo_name: str,
    issues: list[NewIssue],
) -> list[dict]:
    """
    Create new GitHub issues.

    Args:
        github_client: The GitHub client instance
        owner: Repository owner
        repo_name: Repository name
        issues: List of NewIssue instances to create

    Returns:
        List of created issue data
    """
    created_issues = []

    for issue in issues:
        try:
            response = github_client.create_issue(owner, repo_name, issue)
            created_issues.append(response)
            typer.echo(f"✅ Created issue #{response['number']}: {response['title']}")
        except Exception as e:
            issue_title = getattr(issue, "title", "Unknown")
            typer.echo(f"❌ Failed to create issue '{issue_title}': {e}")

    typer.echo(f"🎉 Created {len(created_issues)} issues successfully")
    return created_issues


def update_issues_in_github(
    github_client: GitHubClient,
    issues: list[UpdatedIssue],
    target_project_owner: Optional[str] = None,
    target_project_number: Optional[str] = None,
) -> list[dict]:
    """
    Update existing GitHub issues and their project fields.

    Args:
        github_client: The GitHub client instance
        issues: List of UpdatedIssue instances to update
        target_project_number: Project number to update fields for (optional)

    Returns:
        List of updated issue data
    """
    updated_issues = []

    for issue in issues:
        issue_number = issue.issue_number
        issue_title = getattr(issue, "title", f"Issue #{issue_number}")

        # Extract repository info from the issue URL
        if not issue.url:
            typer.echo(f"❌ No URL found for issue #{issue_number}")
            continue

        try:
            owner, repo_name = extract_repo_from_issue_url(issue.url)
        except ValueError as e:
            typer.echo(f"❌ Invalid URL for issue #{issue_number}: {e}")
            continue

        try:
            # Update the GitHub issue first
            response = github_client.update_issue(owner, repo_name, issue)
            updated_issues.append(response)
            typer.echo(f"✅ Updated issue #{response['number']}: {response['title']}")

            # Update project fields only if target project is specified
            if (
                issue_number is not None
                and target_project_owner
                and target_project_number
                and hasattr(issue, "project_fields")
                and issue.project_fields
            ):
                try:
                    project_results = github_client.update_issue_project_fields(
                        owner,
                        repo_name,
                        issue_number,
                        issue.project_fields,
                        target_project_owner,
                        target_project_number,
                    )

                    # Report successful field updates
                    if project_results.updated_fields:
                        updated_fields = list(project_results.updated_fields.keys())
                        typer.echo(
                            f"  📊 Updated project fields: {', '.join(updated_fields)}"
                        )

                    # Report field update errors
                    if project_results.errors:
                        for field_name, error in project_results.errors.items():
                            typer.echo(f"  ⚠️ Field '{field_name}': {error}")

                except Exception as e:
                    typer.echo(f"  ⚠️ Failed to update project fields: {e}")

        except Exception as e:
            typer.echo(f"❌ Failed to update issue '{issue_title}': {e}")

    typer.echo(f"🎉 Updated {len(updated_issues)} issues successfully")
    return updated_issues
