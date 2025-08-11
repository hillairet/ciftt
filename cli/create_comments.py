import typer

from utils import extract_issue_number, extract_repo_from_issue_url

from .common import (
    handle_cli_error,
    load_csv_for_command,
    setup_github_client_for_command,
)


def create_comments(
    csv_file: str = typer.Argument(
        ..., help="Path to the CSV file containing comment data"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-d", help="Print actions without executing them"
    ),
):
    """
    Create comments on existing GitHub issues from a CSV file.

    CSV format should include URL and Comment columns.
    Optional columns: Author, Date for attribution.
    """
    try:
        csv_data = load_csv_for_command(csv_file)

        _validate_csv_format(csv_data)

        if dry_run:
            _perform_dry_run(csv_data)
            return

        github_client = setup_github_client_for_command(required_scopes=["repo"])

        _create_comments_from_csv(github_client, csv_data)

    except Exception as e:
        handle_cli_error("Comment creation", e)


def _validate_csv_format(csv_data) -> None:
    """
    Validate that the CSV has required columns for comment creation.

    Args:
        csv_data: CSVData object to validate

    Raises:
        ValueError: If required columns are missing
    """
    if "URL" not in csv_data.data.columns:
        raise ValueError("CSV must contain 'URL' column")

    if "Comment" not in csv_data.data.columns:
        raise ValueError("CSV must contain 'Comment' column")

    # Check for empty URLs or comments
    empty_urls = csv_data.data["URL"].isna() | (csv_data.data["URL"] == "")
    if empty_urls.any():
        empty_rows = list(csv_data.data.index[empty_urls] + 1)
        raise ValueError(f"Empty URL values found in rows: {empty_rows}")

    empty_comments = csv_data.data["Comment"].isna() | (csv_data.data["Comment"] == "")
    if empty_comments.any():
        empty_rows = list(csv_data.data.index[empty_comments] + 1)
        raise ValueError(f"Empty Comment values found in rows: {empty_rows}")


def _perform_dry_run(csv_data) -> None:
    """
    Perform a dry run showing what comments would be created.

    Args:
        csv_data: CSVData object with comment data
    """
    typer.echo("🧪 Dry run mode - showing what would be done:")
    typer.echo()

    for index, row in csv_data.data.iterrows():
        try:
            url = row["URL"]
            owner, repo_name = extract_repo_from_issue_url(url)
            issue_number = extract_issue_number(url)

            # Format comment body with attribution if provided
            formatted_comment = _format_comment_body(row)

            typer.echo(f"📝 Would create comment on {owner}/{repo_name}#{issue_number}")
            typer.echo(
                f"   Comment: {formatted_comment[:100]}{'...' if len(formatted_comment) > 100 else ''}"
            )
            typer.echo()

        except Exception as e:
            typer.echo(f"❌ Row {index + 1}: Invalid URL format - {e}")
            typer.echo()


def _create_comments_from_csv(github_client, csv_data) -> None:
    """
    Create comments from CSV data.

    Args:
        github_client: GitHub client for API calls
        csv_data: CSVData object with comment data
    """
    typer.echo(f"💬 Creating comments from {len(csv_data.data)} rows...")
    typer.echo()

    success_count = 0
    error_count = 0

    for index, row in csv_data.data.iterrows():
        try:
            url = row["URL"]
            owner, repo_name = extract_repo_from_issue_url(url)
            issue_number = extract_issue_number(url)

            formatted_comment = _format_comment_body(row)

            # Create the comment
            response = github_client.create_issue_comment(
                owner, repo_name, issue_number, formatted_comment
            )

            comment_id = response.get("id")
            typer.echo(
                f"✅ Created comment {comment_id} on {owner}/{repo_name}#{issue_number}"
            )
            success_count += 1

        except Exception as e:
            typer.echo(f"❌ Row {index + 1}: Failed to create comment - {e}")
            error_count += 1

    typer.echo()
    typer.echo(f"📊 Summary: {success_count} comments created, {error_count} failed")


def _format_comment_body(row) -> str:
    """
    Format comment body with optional author attribution.

    Args:
        row: Pandas Series with comment data

    Returns:
        Formatted comment body string
    """
    comment = str(row["Comment"]).strip()

    # Add attribution if Author or Date columns are present
    attribution_parts = []

    if (
        "Author" in row
        and row["Author"] is not None
        and str(row["Author"]).strip()
        and str(row["Author"]).lower() != "nan"
    ):
        attribution_parts.append(f"Originally by: {str(row['Author']).strip()}")

    if (
        "Date" in row
        and row["Date"] is not None
        and str(row["Date"]).strip()
        and str(row["Date"]).lower() != "nan"
    ):
        attribution_parts.append(f"Date: {str(row['Date']).strip()}")

    if attribution_parts:
        attribution = " | ".join(attribution_parts)
        comment = f"{comment}\n\n*{attribution}*"

    return comment
