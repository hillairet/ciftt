import pandas as pd
import typer

from github import GitHubClient
from settings import Settings
from utils import parse_issue_numbers, parse_repo


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
    project_fields: str = typer.Option(
        None,
        "--fields",
        "-f",
        help="Comma-separated list of GitHub Project v2 fields to include in export",
    ),
):
    """
    Export GitHub issues to a CSV file that can be used for updates.
    """
    settings = Settings()
    
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
    if not issues_data:
        typer.echo("⚠️ No issues found to export")
        raise typer.Exit(code=0)

    # If project fields are requested, fetch them
    project_field_data = {}
    field_names = []
    if project_fields:
        field_names = [field.strip() for field in project_fields.split(",")]
        typer.echo(f"🔍 Fetching project fields: {', '.join(field_names)}")

        # Get issue numbers
        issue_numbers = [issue["number"] for issue in issues_data]

        try:
            project_field_data = github_client.get_project_fields_for_issues(
                owner, repo_name, issue_numbers, field_names
            )
            typer.echo(
                f"✅ Successfully fetched project fields for {len(project_field_data)} issues"
            )
        except Exception as e:
            typer.echo(f"⚠️ Warning: Failed to fetch project fields: {e}")

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

        # Add project fields if available
        if project_fields and issue["number"] in project_field_data:
            for field_name in field_names:
                row[field_name] = project_field_data[issue["number"]].get(
                    field_name, ""
                )

        rows.append(row)

    df = pd.DataFrame(rows)

    # Save to CSV
    try:
        df.to_csv(output_file, index=False)
        typer.echo(f"✅ Successfully exported {len(df)} issues to {output_file}")
    except Exception as e:
        typer.echo(f"❌ Failed to write CSV file: {e}")
        raise typer.Exit(code=1)
