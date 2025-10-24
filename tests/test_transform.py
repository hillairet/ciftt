import tempfile
from pathlib import Path

import pytest

from csv_data import CSVData
from transform import transform_csv_to_new_issues, transform_csv_to_updated_issues


class TestTransformNewIssues:
    """Test transformation of CSV data to NewIssue instances."""

    def test_transform_with_title_whitespace_stripping(self):
        """Test that title whitespace is stripped during transformation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "test.csv"
            csv_path.write_text("Title,Description\n  Test Title  ,Test body")

            csv_data = CSVData(str(csv_path))
            issues = transform_csv_to_new_issues(csv_data.data)

            assert len(issues) == 1
            assert issues[0].title == "Test Title"

    def test_transform_with_empty_title_rejected_at_csv_level(self):
        """Test that empty titles are rejected at CSV loading level."""
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "test.csv"
            csv_path.write_text(
                "Title,Description\n,Test body\nValid Title,Another body"
            )

            # csv_data.py should reject this during loading
            with pytest.raises(ValueError, match="Empty title values found"):
                CSVData(str(csv_path))

    def test_transform_with_empty_title_string_rejected(self):
        """Test that empty title strings are rejected during Pydantic validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "test.csv"
            # Use URL column to bypass csv_data.py validation (it only validates new issues)
            csv_path.write_text(
                "Title,Description,URL\n"
                ",Body,https://github.com/owner/repo/issues/1\n"
                "Valid,Body,https://github.com/owner/repo/issues/2"
            )

            csv_data = CSVData(str(csv_path))
            # Remove URL to treat as new issues, which will trigger Pydantic validation
            csv_data.data = csv_data.data.drop(columns=["URL"])
            issues = transform_csv_to_new_issues(csv_data.data)

            # Should skip the row with empty title via Pydantic validation
            assert len(issues) == 1
            assert issues[0].title == "Valid"

    def test_transform_with_escaped_newlines(self):
        """Test that escaped newlines in body are properly decoded."""
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "test.csv"
            csv_path.write_text("Title,Description\nTest,Line1\\nLine2\\nLine3")

            csv_data = CSVData(str(csv_path))
            issues = transform_csv_to_new_issues(csv_data.data)

            assert len(issues) == 1
            assert issues[0].body == "Line1\nLine2\nLine3"
            assert "\n" in issues[0].body
            assert "\\n" not in issues[0].body

    def test_transform_multiple_issues(self):
        """Test transforming multiple issues from CSV."""
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "test.csv"
            csv_path.write_text(
                "Title,Description,Labels\n"
                "Issue 1,Body 1,bug\n"
                "Issue 2,Body 2,feature\n"
                "Issue 3,Body 3,enhancement"
            )

            csv_data = CSVData(str(csv_path))
            issues = transform_csv_to_new_issues(csv_data.data)

            assert len(issues) == 3
            assert issues[0].title == "Issue 1"
            assert issues[1].title == "Issue 2"
            assert issues[2].title == "Issue 3"


class TestTransformUpdatedIssues:
    """Test transformation of CSV data to UpdatedIssue instances."""

    def test_transform_with_url_extraction(self):
        """Test that issue_number is automatically extracted from URL."""
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "test.csv"
            csv_path.write_text(
                "Title,Description,URL\n"
                "Updated Title,Updated body,https://github.com/owner/repo/issues/123"
            )

            csv_data = CSVData(str(csv_path))
            issues = transform_csv_to_updated_issues(csv_data)

            assert len(issues) == 1
            assert issues[0].issue_number == 123
            assert issues[0].title == "Updated Title"

    def test_transform_with_invalid_url(self):
        """Test that invalid URLs are rejected during transformation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "test.csv"
            csv_path.write_text(
                "Title,Description,URL\n"
                "Title 1,Body 1,https://github.com/owner/repo\n"
                "Title 2,Body 2,https://github.com/owner/repo/issues/456"
            )

            csv_data = CSVData(str(csv_path))
            issues = transform_csv_to_updated_issues(csv_data)

            # Should skip the row with invalid URL and only process valid row
            assert len(issues) == 1
            assert issues[0].issue_number == 456

    def test_transform_with_project_fields(self):
        """Test that project fields are properly extracted and included."""
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "test.csv"
            csv_path.write_text(
                "Title,Description,URL,Sprint,Priority\n"
                "Updated,Body,https://github.com/owner/repo/issues/789,Sprint 1,High"
            )

            csv_data = CSVData(str(csv_path))
            issues = transform_csv_to_updated_issues(csv_data)

            assert len(issues) == 1
            assert issues[0].issue_number == 789
            assert issues[0].project_fields == {
                "Sprint": "Sprint 1",
                "Priority": "High",
            }

    def test_transform_with_body_escape_sequences(self):
        """Test that escape sequences in body are decoded for updated issues."""
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "test.csv"
            csv_path.write_text(
                "Title,Description,URL\n"
                "Test,Line1\\nLine2,https://github.com/owner/repo/issues/999"
            )

            csv_data = CSVData(str(csv_path))
            issues = transform_csv_to_updated_issues(csv_data)

            assert len(issues) == 1
            assert issues[0].body == "Line1\nLine2"
            assert "\n" in issues[0].body

    def test_transform_without_url_rejected(self):
        """Test that rows without URL are rejected for update issues."""
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "test.csv"
            csv_path.write_text(
                "Title,Description,URL\n"
                "No URL,Body without URL,\n"
                "With URL,Body with URL,https://github.com/owner/repo/issues/111"
            )

            csv_data = CSVData(str(csv_path))
            issues = transform_csv_to_updated_issues(csv_data)

            # Should skip the row without URL
            assert len(issues) == 1
            assert issues[0].issue_number == 111
