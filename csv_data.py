"""
CSV data handling module for CIFTT.
Provides a standardized interface for working with CSV/TSV issue data.
"""

import csv
from pathlib import Path

import pandas as pd

from utils import safe_decode


class CSVData:
    """
    Standardized class for handling CSV/TSV data for GitHub issues.
    Abstracts away the pandas DataFrame implementation details.
    """

    def __init__(self, filepath: str, delimiter: str = None):
        self.filepath = Path(filepath)
        self.data = None
        self.delimiter = delimiter
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
            with open(self.filepath, "r", newline="") as file:
                sample = file.read(4096)  # Read a sample of the file
                sniffer = csv.Sniffer()
                dialect = sniffer.sniff(sample)
                return dialect.delimiter
        except:
            # Default to comma if detection fails
            return ","

    def _load_data(self) -> None:
        """Load the CSV/TSV file into a pandas DataFrame."""
        try:
            # Use provided delimiter or detect it
            delimiter = self.delimiter or self._detect_delimiter()
            self.data = pd.read_csv(self.filepath, delimiter=delimiter)
            # Handle \n, \t, \r, etc ... if description column exists
            if "description" in self.data.columns:
                self.data["description"] = self.data["description"].apply(safe_decode)
        except pd.errors.EmptyDataError:
            # Handle empty CSV files with no columns
            self.data = pd.DataFrame()
            raise ValueError("Data file is missing required 'title' column")
        except Exception as e:
            raise ValueError(f"Failed to load data file: {e}")

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
        # Check if there are any new issues (rows without a URL)
        if "URL" in self.data.columns:
            new_issues = self.data["URL"].isna() | (self.data["URL"] == "")
            has_new_issues = new_issues.any()
        else:
            # If there's no URL column, all rows are considered new issues
            has_new_issues = True
            new_issues = pd.Series(True, index=self.data.index)

        # If there are new issues, ensure the 'Title' column exists
        if has_new_issues and "Title" not in self.data.columns:
            raise ValueError(
                "Data file is missing required 'Title' column for new issues"
            )

        if not (has_new_issues and "Title" in self.data.columns):
            return

        # Ensure all new issues have non-empty titles
        empty_titles = (
            self.data["Title"].isna() | (self.data["Title"] == "")
        ) & new_issues

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
            "Assignee",
            "Assignees",
            "Milestone",
            "State",
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
        project_fields = {}

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
