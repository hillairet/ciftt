from typing import Dict, List, Set, Tuple

import typer

from ciftt.utils import (
    extract_issue_number,
    extract_repo_from_issue_url,
    parse_github_project_identifier,
)

from .common import (
    handle_cli_error,
    load_csv_for_command,
    setup_github_client_for_command,
)


def _validate_project_identifier(project_identifier: str) -> Tuple[str, str]:
    try:
        owner, project_number = parse_github_project_identifier(project_identifier)
        return owner, project_number
    except ValueError as e:
        typer.echo(f"❌ Error: {e}")
        raise typer.Exit(code=1) from e


def _extract_repositories_from_csv(csv_data) -> Set[Tuple[str, str]]:
    repositories = set()

    for _, row in csv_data.data.iterrows():
        issue_url = row.get("URL")
        if issue_url:
            try:
                owner, repo_name = extract_repo_from_issue_url(issue_url)
                repositories.add((owner, repo_name))
            except ValueError:
                continue

    return repositories


def _extract_issues_from_csv(csv_data) -> List[Dict[str, any]]:
    issues = []

    for _, row in csv_data.data.iterrows():
        issue_url = row.get("URL")
        if not issue_url:
            continue

        try:
            owner, repo_name = extract_repo_from_issue_url(issue_url)
            issue_number = extract_issue_number(issue_url)

            if not issue_number:
                typer.echo(
                    f"⚠️  Warning: Could not extract issue number from {issue_url}"
                )
                continue

            issues.append(
                {
                    "url": issue_url,
                    "owner": owner,
                    "repo": repo_name,
                    "number": issue_number,
                }
            )
        except ValueError as e:
            typer.echo(f"⚠️  Warning: Skipping invalid URL {issue_url}: {e}")
            continue

    return issues


def _perform_dry_run(
    issues: List[Dict[str, any]], project_owner: str, project_number: str
) -> None:
    typer.echo("🧪 DRY RUN MODE: No changes will be made on GitHub")
    typer.echo(
        f"Would add {len(issues)} issues to project {project_owner}/{project_number}:"
    )
    for issue in issues:
        typer.echo(f"  • {issue['owner']}/{issue['repo']}#{issue['number']}")


def add_to_project(
    csv_file: str = typer.Argument(
        ..., help="Path to the CSV file containing issue URLs"
    ),
    project: str = typer.Argument(
        ..., help="GitHub project (formats: owner/123, owner/projects/123, or full URL)"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-d", help="Print actions without executing them"
    ),
):
    """
    Add GitHub issues to a Project v2 board from a CSV file.
    """
    csv_data = load_csv_for_command(csv_file)

    if "URL" not in csv_data.data.columns:
        typer.echo("❌ Error: CSV must contain a 'URL' column")
        raise typer.Exit(code=1)

    project_owner, project_number = _validate_project_identifier(project)
    typer.echo(f"🎯 Target project: {project_owner}/projects/{project_number}")

    repositories = _extract_repositories_from_csv(csv_data)
    if repositories:
        repo_list = [f"{owner}/{repo}" for owner, repo in repositories]
        typer.echo(f"📂 Repositories found in CSV: {', '.join(repo_list)}")
    else:
        typer.echo("❌ No valid issue URLs found in CSV")
        raise typer.Exit(code=1)

    issues = _extract_issues_from_csv(csv_data)
    if not issues:
        typer.echo("❌ No valid issues found in CSV")
        raise typer.Exit(code=1)

    typer.echo(f"📝 Found {len(issues)} issues to add to project")

    if dry_run:
        _perform_dry_run(issues, project_owner, project_number)
        return

    github_client = setup_github_client_for_command(
        required_scopes=["repo", "project"], repositories=list(repositories)
    )

    try:
        project_info = github_client.validate_project_exists(
            project_owner, project_number
        )
        typer.echo(f"✅ Project validated: {project_info.title} ({project_info.type})")
    except ValueError as e:
        handle_cli_error("Project validation", e)

    typer.echo(f"🚀 Adding {len(issues)} issues to project...")

    added_count = 0
    error_count = 0

    for issue in issues:
        try:
            issue_info = github_client.get_issue_node_id(
                issue["owner"], issue["repo"], issue["number"]
            )

            result = github_client.add_issue_to_project(
                project_info.id, issue_info.id, issue["number"], issue["url"]
            )

            typer.echo(f"✅ Added #{result.issue_number}: {issue_info.title}")
            added_count += 1

        except ValueError as e:
            typer.echo(f"❌ Failed to add {issue['url']}: {e}")
            error_count += 1

    typer.echo(f"\n🎉 Done! Added {added_count} issues to project")
    if error_count > 0:
        typer.echo(f"⚠️  {error_count} issues failed to add")
