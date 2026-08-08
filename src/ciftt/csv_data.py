"""
CSV data handling module for CIFTT.
Provides a standardized interface for working with CSV/TSV issue data.
"""

import csv
from pathlib import Path
from typing import Optional

import pandas as pd


class CSVData:
    """
    Standardized class for handling CSV/TSV data for GitHub issues.
    Abstracts away the pandas DataFrame implementation details.
    """

    def __init__(self, filepath: str, delimiter: Optional[str] = None):
        self.filepath = Path(filepath)
        self.data = pd.DataFrame()
        self.delimiter = delimiter
        self.standard_issue_fields: set[str] = set()
        self.project_field_columns: list[str] = []
        self.issue_field_columns: list[str] = []
        self._load_data()
        self._normalize_column_names()
        self._validate_titles()
        self._identify_column_types()

    def _detect_delimiter(self) -> str:
        """Detect the delimiter used in the file."""
        # First try by file extension
        if self.filepath.suffix.lower() == ".tsv":
            return "\t"
        elif self.filepath.suffix.lower() == ".csv":
            return ","

        # If extension doesn't clearly indicate, try to sniff the delimiter
        try:
            with open(self.filepath, newline="") as file:
                sample = file.read(4096)  # Read a sample of the file
                sniffer = csv.Sniffer()
                dialect = sniffer.sniff(sample)
                return dialect.delimiter
        except Exception:
            # Default to comma if detection fails
            return ","

    def _load_data(self) -> None:
        """Load the CSV/TSV file into a pandas DataFrame."""
        try:
            # Use provided delimiter or detect it
            delimiter = self.delimiter or self._detect_delimiter()
            self.data = pd.read_csv(self.filepath, delimiter=delimiter)
        except pd.errors.EmptyDataError as e:
            # Handle empty CSV files with no columns
            self.data = pd.DataFrame()
            raise ValueError("Data file is missing required 'title' column") from e
        except Exception as e:
            raise ValueError(f"Failed to load data file: {e}") from e

    def _normalize_column_names(self) -> None:
        """
        Ensure required columns exist for processing.
        """
        # Ensure 'URL' column exists if not present
        if "URL" not in self.data.columns:
            self.data["URL"] = None

    def _validate_titles(self) -> None:
        """
        Validate that:
        1. If there are any new issues (rows without a URL), the 'title' column must exist
        2. All new issues must have non-empty title values
        """
        new_issues_mask = self._identify_new_issues()
        has_new_issues = bool(new_issues_mask.any())

        self._validate_title_column_exists(has_new_issues)

        if has_new_issues and "Title" in self.data.columns:
            self._validate_title_values(new_issues_mask)

    def _identify_new_issues(self) -> pd.Series:
        """
        Identify which rows represent new issues (rows without URLs).

        Returns:
            Boolean Series indicating which rows are new issues
        """
        if "URL" in self.data.columns:
            return self.data["URL"].isna() | (self.data["URL"] == "")
        else:
            # If there's no URL column, all rows are considered new issues
            return pd.Series(True, index=self.data.index)

    def _validate_title_column_exists(self, has_new_issues: bool) -> None:
        """
        Validate that Title column exists when there are new issues.

        Args:
            has_new_issues: Whether there are any new issues in the data

        Raises:
            ValueError: If Title column is missing but required
        """
        if has_new_issues and "Title" not in self.data.columns:
            raise ValueError(
                "Data file is missing required 'Title' column for new issues"
            )

    def _validate_title_values(self, new_issues_mask: pd.Series) -> None:
        """
        Validate that all new issues have non-empty title values.

        Args:
            new_issues_mask: Boolean Series indicating which rows are new issues

        Raises:
            ValueError: If any new issues have empty titles
        """
        empty_titles = (
            self.data["Title"].isna() | (self.data["Title"] == "")
        ) & new_issues_mask

        if empty_titles.any():
            empty_rows = list(
                self.data.index[empty_titles] + 1
            )  # +1 for human-readable row numbers
            raise ValueError(
                f"Empty title values found for new issues in rows: {empty_rows}"
            )

    def _identify_column_types(self) -> None:
        """
        Identify which columns are standard issue fields vs project fields.

        Standard issue fields are predefined GitHub issue attributes.
        Project fields are custom fields from GitHub Projects v2.
        """
        # Define standard GitHub issue fields (case-sensitive)
        self.standard_issue_fields = {
            "Title",
            "Description",
            "Body",
            "Labels",
            "Assignees",
            "Milestone",
            "State",
            "StateReason",
            "URL",
            "Number",
            "Created_at",
            "Updated_at",
            "Closed_at",
            "Author",
            "Locked",
        }

        # Identify project fields (columns that aren't standard issue fields)
        # All columns are now case-sensitive
        self.project_field_columns = []
        self.issue_field_columns = []

        for col in self.data.columns:
            if col in self.standard_issue_fields:
                self.issue_field_columns.append(col)
            else:
                # All project field columns use original case
                self.project_field_columns.append(col)

    def get_project_field_data(self, row_index: int) -> dict:
        """
        Extract project field values from a specific row.

        Args:
            row_index: Row index in the DataFrame

        Returns:
            Dictionary mapping project field names to their values
        """
        project_fields: dict[str, str] = {}

        if row_index >= len(self.data):
            return project_fields

        row = self.data.iloc[row_index]

        for field_name in self.project_field_columns:
            # Access DataFrame using original case column names
            value = row.get(field_name)
            if pd.notna(value) and str(value).strip():  # Only include non-empty values
                project_fields[field_name] = str(value).strip()

        return project_fields

    def has_project_fields(self) -> bool:
        """
        Check if the CSV contains any project field columns.

        Returns:
            True if there are project field columns, False otherwise
        """
        return len(self.project_field_columns) > 0
