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
        Normalize column names to lowercase for case-insensitive matching.
        Creates a mapping from lowercase to original column names.
        """
        # Create a mapping of lowercase column names to original column names
        self.column_map = {col.lower(): col for col in self.data.columns}

        # Rename columns to lowercase
        self.data.columns = [col.lower() for col in self.data.columns]

        # Ensure 'url' column exists
        if "url" not in self.data.columns:
            self.data["url"] = None

    def _validate_titles(self) -> None:
        """
        Validate that:
        1. If there are any new issues (rows without a URL), the 'title' column must exist
        2. All new issues must have non-empty title values
        """
        # Check if there are any new issues (rows without a URL)
        if "url" in self.data.columns:
            new_issues = self.data["url"].isna() | (self.data["url"] == "")
            has_new_issues = new_issues.any()
        else:
            # If there's no URL column, all rows are considered new issues
            has_new_issues = True
            new_issues = pd.Series(True, index=self.data.index)

        # If there are new issues, ensure the 'title' column exists
        if has_new_issues and "title" not in self.data.columns:
            raise ValueError(
                "Data file is missing required 'title' column for new issues"
            )

        # If there are new issues and a title column, ensure all new issues have non-empty titles
        if has_new_issues and "title" in self.data.columns:
            empty_titles = (
                self.data["title"].isna() | (self.data["title"] == "")
            ) & new_issues

            if empty_titles.any():
                empty_rows = list(
                    self.data.index[empty_titles] + 1
                )  # +1 for human-readable row numbers
                raise ValueError(
                    f"Empty title values found for new issues in rows: {empty_rows}"
                )
