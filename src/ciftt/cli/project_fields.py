import typer

from ciftt.github import GitHubClient


def fetch_github_project_fields(
    github_client: GitHubClient,
    owner: str,
    repo_name: str,
    issues_data: list,
    project_fields: str,
) -> tuple[dict, list]:
    """
    Fetch GitHub project fields for issues.

    Args:
        github_client: GitHub client instance
        owner: Repository owner
        repo_name: Repository name
        issues_data: List of issue data
        project_fields: Comma-separated list of field names

    Returns:
        Tuple of (project_field_data dict, field_names list)
    """
    project_field_data: dict = {}
    field_names: list[str] = []

    if not project_fields:
        return project_field_data, field_names

    field_names = [field.strip() for field in project_fields.split(",")]
    issue_numbers = [issue["number"] for issue in issues_data]
    typer.echo(
        f"🔍 Fetching project fields for {len(issue_numbers)} issues: "
        f"{', '.join(field_names)}"
    )

    def report_progress(completed: int, total: int, issue_number: int) -> None:
        if completed != 1 and completed % 25 != 0 and completed != total:
            return

        typer.echo(
            f"⏳ Fetched project fields for {completed}/{total} issues "
            f"(latest: #{issue_number})"
        )

    try:
        project_field_data = github_client.get_project_fields_for_issues(
            owner,
            repo_name,
            issue_numbers,
            field_names,
            progress_callback=report_progress,
        )
        typer.echo(
            f"✅ Successfully fetched project fields for {len(project_field_data)} issues"
        )
    except Exception as e:
        typer.echo(f"⚠️ Warning: Failed to fetch project fields: {e}")

    return project_field_data, field_names
