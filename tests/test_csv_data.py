import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from csv_data import CSVData


@pytest.fixture
def sample_csv_path():
    """Create a temporary CSV file with just the title column."""
    with tempfile.TemporaryDirectory() as temp_dir:
        csv_path = Path(temp_dir) / "test_issues.csv"
        
        # Create sample data with only the title column
        sample_data = pd.DataFrame({
            "title": [
                "Fix login button on homepage",
                "Update documentation for API v2",
                "Add dark mode support"
            ]
        })
        
        # Save to CSV
        sample_data.to_csv(csv_path, index=False)
        
        yield csv_path


@pytest.fixture
def empty_csv_with_title_column():
    """Create an empty CSV file with just the title column."""
    with tempfile.TemporaryDirectory() as temp_dir:
        csv_path = Path(temp_dir) / "empty.csv"
        pd.DataFrame(columns=["title"]).to_csv(csv_path, index=False)
        yield csv_path


@pytest.fixture
def empty_csv_no_columns():
    """Create a truly empty CSV file (no columns)."""
    with tempfile.TemporaryDirectory() as temp_dir:
        csv_path = Path(temp_dir) / "no_columns.csv"
        with open(csv_path, "w") as f:
            f.write("")
        yield csv_path


def test_load_minimal_csv(sample_csv_path):
    """Test loading a CSV with only the required title column."""
    csv_data = CSVData(sample_csv_path)
    
    # Check that data was loaded correctly
    assert csv_data.data is not None
    assert len(csv_data.data) == 3
    assert "title" in csv_data.data.columns
    
    # Verify the titles were loaded correctly
    expected_titles = [
        "Fix login button on homepage",
        "Update documentation for API v2",
        "Add dark mode support"
    ]
    assert csv_data.data["title"].tolist() == expected_titles


def test_empty_csv_with_title(empty_csv_with_title_column):
    """Test that an empty CSV with title column loads without error."""
    # Should not raise an error as it has the required column
    csv_data = CSVData(empty_csv_with_title_column)
    assert len(csv_data.data) == 0


def test_empty_csv_no_columns(empty_csv_no_columns):
    """Test that a CSV without a title column raises an error."""
    # Should raise a ValueError due to missing title column
    with pytest.raises(ValueError, match="missing required 'title' column"):
        CSVData(empty_csv_no_columns)
