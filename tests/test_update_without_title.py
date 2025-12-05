import tempfile
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest
import typer

from ciftt.cli.dry_run import perform_dry_run
from ciftt.csv_data import CSVData


@pytest.fixture
def csv_with_urls_no_title():
    """Create a CSV with URLs but no Title column - for updating existing issues."""
    with tempfile.TemporaryDirectory() as temp_dir:
        csv_path = Path(temp_dir) / "update_no_title.csv"

        sample_data = pd.DataFrame(
            {
                "URL": [
                    "https://github.com/owner/repo/issues/1",
                    "https://github.com/owner/repo/issues/2",
                ],
                "State": ["closed", "closed"],
                "Labels": ["bug,fixed", "enhancement"],
            }
        )

        sample_data.to_csv(csv_path, index=False)
        yield csv_path


@pytest.fixture
def csv_mixed_with_and_without_url():
    """Create a CSV with some new issues (no URL) and some updates (with URL)."""
    with tempfile.TemporaryDirectory() as temp_dir:
        csv_path = Path(temp_dir) / "mixed.csv"

        sample_data = pd.DataFrame(
            {
                "URL": [
                    "https://github.com/owner/repo/issues/1",
                    "",  # New issue without URL
                ],
                "Title": ["Existing issue", "New issue"],
                "State": ["closed", "open"],
            }
        )

        sample_data.to_csv(csv_path, index=False)
        yield csv_path


@pytest.fixture
def csv_new_issues_no_title():
    """Create a CSV with new issues (no URLs) but missing Title column."""
    with tempfile.TemporaryDirectory() as temp_dir:
        csv_path = Path(temp_dir) / "new_no_title.csv"

        sample_data = pd.DataFrame(
            {
                "Description": ["This is a description"],
                "Labels": ["bug"],
            }
        )

        sample_data.to_csv(csv_path, index=False)
        yield csv_path


def test_update_issues_without_title_column(csv_with_urls_no_title):
    """
    Test that we can load CSV for updating existing issues without a Title column.
    When all rows have URLs (existing issues), Title should be optional.
    """
    csv_data = CSVData(csv_with_urls_no_title)

    assert csv_data.data is not None
    assert len(csv_data.data) == 2
    assert "URL" in csv_data.data.columns
    assert "State" in csv_data.data.columns
    assert "Title" not in csv_data.data.columns


def test_mixed_new_and_update_requires_title(csv_mixed_with_and_without_url):
    """
    Test that when there are new issues (rows without URLs), Title is required.
    """
    csv_data = CSVData(csv_mixed_with_and_without_url)

    assert csv_data.data is not None
    assert "Title" in csv_data.data.columns


def test_new_issues_without_title_raises_error(csv_new_issues_no_title):
    """
    Test that new issues (no URLs) without Title column raises an error.
    """
    with pytest.raises(
        ValueError, match="missing required 'Title' column for new issues"
    ):
        CSVData(csv_new_issues_no_title)


def test_dry_run_without_title_column(csv_with_urls_no_title, capsys):
    """
    Test that dry-run works correctly when Title column is missing.
    This was a bug - dry-run assumed Title column always exists.
    """
    csv_data = CSVData(csv_with_urls_no_title)

    perform_dry_run(csv_data)

    captured = capsys.readouterr()
    assert "Would update issue #1: (no title change)" in captured.out
    assert "Would update issue #2: (no title change)" in captured.out
    assert "DRY RUN MODE" in captured.out
