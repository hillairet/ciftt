import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import typer

from ciftt.utils import IssueUrlParts, parse_github_issue_or_pull_url


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
            url = row.get("URL") or ""
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
