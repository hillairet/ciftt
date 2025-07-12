from typing import List, Tuple

import typer

from github import GitHubClient, NewIssue, UpdatedIssue


def create_or_update_issues(
    github_client: GitHubClient, 
    owner: str, 
    repo_name: str, 
    issues: List[NewIssue | UpdatedIssue]
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
