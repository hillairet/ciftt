import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import typer

from ciftt.cli.common import handle_cli_error, setup_github_client_for_command
from ciftt.github.client import GitHubClient
from ciftt.github.data import UpdatedIssue
from ciftt.utils import (
    IssueUrlParts,
    parse_github_issue_or_pull_url,
    parse_repo,
    safe_decode,
)


@dataclass
class TransferRow:
    source_url: str
    row: Dict[str, Any]
    source_parts: IssueUrlParts
    destination_url: Optional[str] = None
    destination_node_id: Optional[str] = None
    parent_number: Optional[int] = None


def _detect_delimiter(path: str) -> str:
    return "\t" if Path(path).suffix.lower() == ".tsv" else ","


def _load_transfer_rows(input_file: str) -> tuple[list[str], list[TransferRow], str]:
    delimiter = _detect_delimiter(input_file)
    rows = []
    with open(input_file, newline="", encoding="utf-8") as file_obj:
        reader = csv.DictReader(file_obj, delimiter=delimiter)
        headers = list(reader.fieldnames or [])
        if "URL" not in headers:
            raise ValueError("URL column is required for transfer-issues")

        for row in reader:
            url = safe_decode(row.get("URL") or "")
            parts = parse_github_issue_or_pull_url(url)
            if parts.kind == "pull":
                typer.echo(f"⚠️ Skipping pull request URL: {url}")
                continue
            rows.append(TransferRow(source_url=url, row=row, source_parts=parts))

    return headers, rows, delimiter


def _load_existing_output_urls(output_file: str, target_repo: str) -> dict[str, str]:
    path = Path(output_file)
    if not path.exists():
        return {}

    delimiter = _detect_delimiter(output_file)
    target_owner, target_name = target_repo.split("/", 1)
    mapped_urls = {}
    with open(path, newline="", encoding="utf-8") as file_obj:
        reader = csv.DictReader(file_obj, delimiter=delimiter)
        for index, row in enumerate(reader, start=1):
            url = row.get("URL") or ""
            try:
                parts = parse_github_issue_or_pull_url(url)
            except ValueError:
                continue
            if parts.kind != "issue":
                continue
            if parts.owner == target_owner and parts.repo == target_name:
                mapped_urls[str(index)] = url

    return mapped_urls


def _strip_output_columns(headers: list[str]) -> list[str]:
    return [header for header in headers if header != "Assignee"]


def _closed_issue_transfer_comment(target_repo: str) -> str:
    return (
        "Temporarily reopening to transfer this issue to "
        f"`{target_repo}` because GitHub's API requires open issues for transfers. "
        "It will be reclosed automatically."
    )


def _patch_destination_description_if_needed(
    github_client: GitHubClient, row: TransferRow
) -> bool:
    description = row.row.get("Description")
    if description is None or str(description).strip() == "":
        return False

    if not row.destination_url:
        return False

    destination_parts = parse_github_issue_or_pull_url(row.destination_url)
    issue_update = UpdatedIssue(
        URL=row.destination_url,
        Description=safe_decode(str(description)),
    )
    github_client.update_issue(
        destination_parts.owner, destination_parts.repo, issue_update
    )
    return True


def _repositories_from_rows(
    rows: list[TransferRow], target_repo: str
) -> list[tuple[str, str]]:
    repositories = {(row.source_parts.owner, row.source_parts.repo) for row in rows}
    repositories.add(parse_repo(target_repo))
    return sorted(repositories)


def _write_transfer_output(
    output_file: str, headers: list[str], rows: list[TransferRow], delimiter: str
) -> None:
    output_headers = _strip_output_columns(headers)
    with open(output_file, "w", newline="", encoding="utf-8") as file_obj:
        writer = csv.DictWriter(
            file_obj,
            fieldnames=output_headers,
            delimiter=delimiter,
            extrasaction="ignore",
        )
        writer.writeheader()
        for transfer_row in rows:
            if not transfer_row.destination_url:
                continue
            output_row = dict(transfer_row.row)
            output_row["URL"] = transfer_row.destination_url
            writer.writerow(output_row)


def _transfer_rows(
    github_client: GitHubClient,
    rows: list[TransferRow],
    target_repo: str,
    target_repo_id: str,
    limit: int,
    existing_output_urls: dict[str, str],
    dry_run: bool,
) -> tuple[int, int, int]:
    transferred = 0
    skipped = 0
    errors = 0

    for index, row in enumerate(rows, start=1):
        existing_url = existing_output_urls.get(str(index))
        if existing_url:
            row.destination_url = existing_url
            _patch_destination_description_if_needed(github_client, row)
            typer.echo(f"⏭️ Row {index}: already transferred -> {existing_url}")
            skipped += 1
            continue

        if limit > 0 and transferred >= limit:
            typer.echo(f"⏹️ Reached --limit {limit}")
            break

        if dry_run:
            typer.echo(f"DRY RUN: Would transfer {row.source_url} -> {target_repo}")
            skipped += 1
            continue

        try:
            info = github_client.get_transfer_issue_info(
                row.source_parts.owner, row.source_parts.repo, row.source_parts.number
            )
            row.parent_number = info.parent_number
            was_closed = info.state == "CLOSED"
            if was_closed:
                github_client.comment_issue(
                    info.id, _closed_issue_transfer_comment(target_repo)
                )
                github_client.reopen_issue(info.id)

            destination = github_client.transfer_issue(info.id, target_repo_id)

            if was_closed:
                github_client.close_issue(destination.id)

            row.destination_url = destination.url
            row.destination_node_id = destination.id
            _patch_destination_description_if_needed(github_client, row)
            transferred += 1
            typer.echo(f"✅ Transferred {row.source_url} -> {destination.url}")
        except Exception as exc:
            errors += 1
            typer.echo(f"❌ Failed to transfer {row.source_url}: {exc}")

    return transferred, skipped, errors


def transfer_issues(
    input_file: str = typer.Argument(..., help="Path to the input CSV/TSV file"),
    output_file: str = typer.Argument(..., help="Path to write transferred CSV/TSV"),
    target_repo: str = typer.Argument(
        ..., help="Target repository in owner/repo format"
    ),
    limit: int = typer.Option(
        0,
        "--limit",
        min=0,
        help="Stop after N newly transferred issues; 0 is unlimited",
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-d", help="Print actions without transferring issues"
    ),
):
    """Transfer GitHub issues to another repository and write destination URLs."""
    try:
        target_owner, target_name = parse_repo(target_repo)
        headers, rows, delimiter = _load_transfer_rows(input_file)
        existing_output_urls = _load_existing_output_urls(output_file, target_repo)
    except Exception as exc:
        handle_cli_error("Transfer setup", exc)

    repositories = _repositories_from_rows(rows, target_repo)
    github_client = setup_github_client_for_command(
        required_scopes=["repo"], repositories=repositories
    )

    try:
        target_repo_id = github_client.get_repository_node_id(target_owner, target_name)
        transferred, skipped, errors = _transfer_rows(
            github_client,
            rows,
            target_repo,
            target_repo_id,
            limit,
            existing_output_urls,
            dry_run,
        )
        if not dry_run:
            _write_transfer_output(output_file, headers, rows, delimiter)
    except Exception as exc:
        handle_cli_error("Transfer", exc)

    typer.echo(
        f"🎉 Transfer complete. Transferred: {transferred}; skipped: {skipped}; errors: {errors}"
    )
    if errors:
        raise typer.Exit(code=1)
