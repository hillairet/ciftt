"""
CSV data handling module for CIFTT.
Provides a standardized interface for working with CSV/TSV issue data.
"""
from pathlib import Path
import csv

import pandas as pd


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
        if self.filepath.suffix.lower() == '.tsv':
            return '\t'
        elif self.filepath.suffix.lower() == '.csv':
            return ','
        
        # If extension doesn't clearly indicate, try to sniff the delimiter
        try:
            with open(self.filepath, 'r', newline='') as file:
                sample = file.read(4096)  # Read a sample of the file
                sniffer = csv.Sniffer()
                dialect = sniffer.sniff(sample)
                return dialect.delimiter
        except:
            # Default to comma if detection fails
            return ','
    
    def _load_data(self) -> None:
        """Load the CSV/TSV file into a pandas DataFrame."""
        try:
            # Use provided delimiter or detect it
            delimiter = self.delimiter or self._detect_delimiter()
            self.data = pd.read_csv(self.filepath, delimiter=delimiter)
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
    
    def _validate_titles(self) -> None:
        """
        Validate that the 'title' column exists and all values are 
        non-empty strings.
        """
        if 'title' not in self.data.columns:
            raise ValueError("Data file is missing required 'title' column")
        
        # Check that all titles are non-empty strings
        empty_titles = self.data['title'].isna() | (self.data['title'] == '')
        if empty_titles.any():
            empty_rows = list(self.data.index[empty_titles] + 1)  # +1 for human-readable row numbers
            raise ValueError(f"Empty title values found in rows: {empty_rows}")
