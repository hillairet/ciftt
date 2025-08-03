from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from click.exceptions import Exit

from cli.update_issues import update_issues
from github.data import ProjectFieldUpdateResult, ProjectInfo


class TestUpdateIssuesIntegration:
    """Integration tests for the update_issues command."""

    def test_update_issues_success(self, fixtures_dir, mock_github_client):
        """Test successful updating of issues from CSV."""
        csv_file = str(fixtures_dir / "update_issues.csv")

        # Mock project validation
        mock_github_client.validate_project_exists.return_value = ProjectInfo(
            id="test-id",
            title="Test Project", 
            number=123,
            url="https://github.com/users/owner/projects/123",
            owner="owner",
            type="user"
        )

        with patch(
            "cli.update_issues.init_github_client", return_value=mock_github_client
        ), patch("cli.update_issues.validate_token_scopes"), patch(
            "cli.update_issues.validate_repository_access"
        ):

            # This should not raise any exceptions
            update_issues(csv_file, "owner/123", dry_run=False)

            # Verify that update_issue was called for each row in the CSV
            assert mock_github_client.update_issue.call_count == 3

    def test_update_issues_dry_run(self, fixtures_dir, capsys):
        """Test dry run mode for update issues."""
        csv_file = str(fixtures_dir / "update_issues.csv")

        # Dry run should not require GitHub client
        update_issues(csv_file, "owner/123", dry_run=True)

        # Check that dry run output was printed
        captured = capsys.readouterr()
        assert "DRY RUN MODE" in captured.out
        assert "Would update issue #123" in captured.out
        assert "Would update issue #124" in captured.out
        assert "Would update issue #125" in captured.out

    def test_update_issues_invalid_csv_no_url(self, tmp_path):
        """Test handling of CSV without URL column for updates."""
        # Create a CSV without URL column (required for updates)
        invalid_csv = tmp_path / "no_url.csv"
        invalid_csv.write_text("title,description\nTest title,Test description")

        with pytest.raises(Exit):  # typer.Exit raises click.exceptions.Exit
            update_issues(str(invalid_csv), "owner/123", dry_run=False)

    def test_update_issues_invalid_project_format(self, fixtures_dir):
        """Test handling of invalid project format."""
        csv_file = str(fixtures_dir / "update_issues.csv")

        with pytest.raises(Exit):  # typer.Exit raises click.exceptions.Exit
            update_issues(csv_file, "invalid-project-format", dry_run=False)

    def test_update_issues_github_api_error(self, fixtures_dir, mock_github_client):
        """Test handling of GitHub API errors during issue updates."""
        csv_file = str(fixtures_dir / "update_issues.csv")

        # Mock project validation
        mock_github_client.validate_project_exists.return_value = ProjectInfo(
            id="test-id",
            title="Test Project", 
            number=123,
            url="https://github.com/users/owner/projects/123",
            owner="owner",
            type="user"
        )

        # Mock GitHub client to raise an exception
        mock_github_client.update_issue.side_effect = Exception("API Error")

        with patch(
            "cli.update_issues.init_github_client", return_value=mock_github_client
        ), patch("cli.update_issues.validate_token_scopes"), patch(
            "cli.update_issues.validate_repository_access"
        ):

            # Should handle the error gracefully and continue with other issues
            update_issues(csv_file, "owner/123", dry_run=False)

            # Verify that update_issue was attempted for each row
            assert mock_github_client.update_issue.call_count == 3

    def test_update_issues_invalid_url_format(self, tmp_path):
        """Test handling of invalid URL format in CSV."""
        # Create a CSV with invalid URL format
        invalid_csv = tmp_path / "invalid_url.csv"
        invalid_csv.write_text(
            "title,description,url\nTest title,Test description,not-a-github-url"
        )

        with patch("cli.update_issues.init_github_client"), patch(
            "cli.update_issues.validate_token_scopes"
        ), patch("cli.update_issues.validate_repository_access"):

            # Should handle invalid URLs gracefully
            with pytest.raises(Exit):  # Should exit when no valid URLs found
                update_issues(str(invalid_csv), "owner/123", dry_run=False)

    def test_update_issues_with_project_fields(self, tmp_path, mock_github_client):
        """Test updating issues with project fields."""
        # Create CSV with project fields
        csv_with_fields = tmp_path / "project_fields.csv"
        csv_with_fields.write_text(
            "Title,URL,Priority,Status\n"
            "Test Issue,https://github.com/owner/repo/issues/123,High,In Progress\n"
        )

        # Mock project validation
        mock_github_client.validate_project_exists.return_value = ProjectInfo(
            id="test-id",
            title="Test Project", 
            number=123,
            url="https://github.com/users/owner/projects/123",
            owner="owner",
            type="user"
        )

        # Mock project field definitions
        mock_github_client.get_project_field_definitions.return_value = {
            "Priority": {"name": "Priority", "dataType": "SINGLE_SELECT"},
            "Status": {"name": "Status", "dataType": "SINGLE_SELECT"},
        }

        # Mock project field update method
        mock_github_client.update_issue_project_fields.return_value = ProjectFieldUpdateResult(
            updated_fields={"Priority": "High", "Status": "In Progress"},
            errors={}
        )

        with patch(
            "cli.update_issues.init_github_client", return_value=mock_github_client
        ), patch("cli.update_issues.validate_token_scopes"), patch(
            "cli.update_issues.validate_repository_access"
        ):

            # Should update both issue and project fields
            update_issues(
                str(csv_with_fields),
                "https://github.com/users/owner/projects/123",
                dry_run=False,
            )

            # Verify issue update was called
            assert mock_github_client.update_issue.call_count == 1

            # Verify project field update was called
            assert mock_github_client.update_issue_project_fields.call_count == 1

            # Check the project fields passed to the update method
            call_args = mock_github_client.update_issue_project_fields.call_args
            assert call_args[0][0] == "owner"  # owner
            assert call_args[0][1] == "repo"  # repo
            assert call_args[0][2] == 123  # issue_number

            # Check the project fields data
            project_fields = call_args[0][3]
            assert project_fields["Priority"] == "High"
            assert project_fields["Status"] == "In Progress"
