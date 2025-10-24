import tempfile
from pathlib import Path

import pytest

from csv_data import CSVData


@pytest.fixture
def csv_with_project_fields():
    """Create a temporary CSV file with project fields."""
    with tempfile.TemporaryDirectory() as temp_dir:
        csv_path = Path(temp_dir) / "project_fields.csv"

        # Create CSV with standard issue fields + project fields
        csv_content = """Title,Description,URL,Priority,Status,Sprint,Assignee Team
Fix login bug,Authentication is broken,https://github.com/owner/repo/issues/123,High,In Progress,Sprint 5,Backend Team
Add dark mode,Implement dark theme support,https://github.com/owner/repo/issues/124,Medium,Backlog,Sprint 6,Frontend Team
Update docs,Documentation needs refresh,https://github.com/owner/repo/issues/125,Low,Done,Sprint 4,DevOps Team"""

        csv_path.write_text(csv_content)
        yield csv_path


@pytest.fixture
def csv_without_project_fields():
    """Create a temporary CSV file with only standard issue fields."""
    with tempfile.TemporaryDirectory() as temp_dir:
        csv_path = Path(temp_dir) / "standard_fields.csv"

        # Create CSV with only standard GitHub issue fields
        csv_content = """Title,Description,Labels,Assignee,URL
Fix login bug,Authentication is broken,bug;high-priority,john-doe,https://github.com/owner/repo/issues/123
Add dark mode,Implement dark theme support,enhancement;ui,jane-smith,https://github.com/owner/repo/issues/124"""

        csv_path.write_text(csv_content)
        yield csv_path


def test_project_field_detection(csv_with_project_fields):
    """Test that project fields are correctly identified."""
    csv_data = CSVData(csv_with_project_fields)

    # Check standard issue fields were detected
    expected_standard = ["Title", "Description", "URL"]
    assert all(field in csv_data.issue_field_columns for field in expected_standard)

    # Check project fields were detected
    expected_project = ["Priority", "Status", "Sprint", "Assignee Team"]
    assert all(field in csv_data.project_field_columns for field in expected_project)

    # Verify has_project_fields returns True
    assert csv_data.has_project_fields() is True


def test_no_project_fields(csv_without_project_fields):
    """Test behavior when no project fields are present."""
    csv_data = CSVData(csv_without_project_fields)

    # Check that all columns are classified as standard issue fields
    expected_standard = ["Title", "Description", "Labels", "Assignee", "URL"]
    assert all(field in csv_data.issue_field_columns for field in expected_standard)

    # Check no project fields detected
    assert len(csv_data.project_field_columns) == 0

    # Verify has_project_fields returns False
    assert csv_data.has_project_fields() is False


def test_get_project_field_data(csv_with_project_fields):
    """Test extraction of project field values from specific rows."""
    csv_data = CSVData(csv_with_project_fields)

    # Test first row
    row_0_fields = csv_data.get_project_field_data(0)
    expected_row_0 = {
        "Priority": "High",
        "Status": "In Progress",
        "Sprint": "Sprint 5",
        "Assignee Team": "Backend Team",
    }
    assert row_0_fields == expected_row_0

    # Test second row
    row_1_fields = csv_data.get_project_field_data(1)
    expected_row_1 = {
        "Priority": "Medium",
        "Status": "Backlog",
        "Sprint": "Sprint 6",
        "Assignee Team": "Frontend Team",
    }
    assert row_1_fields == expected_row_1

    # Test invalid row index
    invalid_row_fields = csv_data.get_project_field_data(999)
    assert invalid_row_fields == {}


def test_case_sensitive_field_classification():
    """Test that field classification works with proper case."""
    with tempfile.TemporaryDirectory() as temp_dir:
        csv_path = Path(temp_dir) / "case_test.csv"

        # Standard issue fields in proper case + project fields
        csv_content = """Title,Description,URL,Priority,Custom Field
Test Issue,Test description,https://github.com/owner/repo/issues/1,High,Value1"""

        csv_path.write_text(csv_content)
        csv_data = CSVData(csv_path)

        # Standard fields should be detected with proper case
        assert "Title" in csv_data.issue_field_columns
        assert "Description" in csv_data.issue_field_columns
        assert "URL" in csv_data.issue_field_columns

        # Project fields should be detected
        assert "Priority" in csv_data.project_field_columns
        assert "Custom Field" in csv_data.project_field_columns


def test_empty_project_field_values():
    """Test handling of empty/null project field values."""
    with tempfile.TemporaryDirectory() as temp_dir:
        csv_path = Path(temp_dir) / "empty_fields.csv"

        csv_content = """Title,URL,Priority,Status
Test Issue,https://github.com/owner/repo/issues/1,High,
Another Issue,https://github.com/owner/repo/issues/2,,In Progress"""

        csv_path.write_text(csv_content)
        csv_data = CSVData(csv_path)

        # First row - only Priority has value
        row_0_fields = csv_data.get_project_field_data(0)
        assert row_0_fields == {"Priority": "High"}

        # Second row - only Status has value
        row_1_fields = csv_data.get_project_field_data(1)
        assert row_1_fields == {"Status": "In Progress"}
