"""
CSV data handling module for CIFTT.
Provides a standardized interface for working with CSV issue data.
"""
from pathlib import Path

import pandas as pd


class CSVData:
    """
    Standardized class for handling CSV data for GitHub issues.
    Abstracts away the pandas DataFrame implementation details.
    """
    def __init__(self, filepath: str):
        self.filepath = Path(filepath)
        self.data = None
        self._load_data()
        self._validate_titles()
    
    def _load_data(self) -> None:
        """Load the CSV file into a pandas DataFrame."""
        try:
            self.data = pd.read_csv(self.filepath)
        except Exception as e:
            raise ValueError(f"Failed to load CSV file: {e}")
    
    def _validate_titles(self) -> None:
        """
        Validate that the 'title' column exists and all values are 
        non-empty strings.
        """
        if 'title' not in self.data.columns:
            raise ValueError("CSV is missing required 'title' column")
        
        # Check that all titles are non-empty strings
        empty_titles = self.data['title'].isna() | (self.data['title'] == '')
        if empty_titles.any():
            empty_rows = list(self.data.index[empty_titles] + 1)  # +1 for human-readable row numbers
            raise ValueError(f"Empty title values found in rows: {empty_rows}")
