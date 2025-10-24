from unittest.mock import patch

import pytest
from click.exceptions import Exit

from cli.create_issues import create_issues


class TestCreateIssuesIntegration:
    """Integration tests for the create_issues command."""

    def test_create_issues_success(self, fixtures_dir, mock_github_client):
        """Test successful creation of issues from CSV."""
        csv_file = str(fixtures_dir / "create_issues.csv")

        with patch(
            "cli.common.init_github_client", return_value=mock_github_client
        ), patch("cli.common.validate_token_scopes"), patch(
            "cli.common.validate_repository_access"
        ):
            # This should not raise any exceptions
            create_issues(csv_file, "owner/repo", dry_run=False)

            # Verify that create_issue was called for each row in the CSV
            assert mock_github_client.create_issue.call_count == 3

    def test_create_issues_dry_run(self, fixtures_dir, capsys):
        """Test dry run mode for create issues."""
        csv_file = str(fixtures_dir / "create_issues.csv")

        # Dry run should not require GitHub client
        create_issues(csv_file, "owner/repo", dry_run=True)

        # Check that dry run output was printed
        captured = capsys.readouterr()
        assert "DRY RUN MODE" in captured.out
        assert "Would create issue: Fix login button on homepage" in captured.out
        assert "Would create issue: Update documentation for API v2" in captured.out
        assert "Would create issue: Add dark mode support" in captured.out

    def test_create_issues_invalid_csv(self, tmp_path):
        """Test handling of invalid CSV file."""
        # Create an invalid CSV (missing title column)
        invalid_csv = tmp_path / "invalid.csv"
        invalid_csv.write_text("description,labels\nTest description,bug")

        with pytest.raises(Exit):  # typer.Exit raises click.exceptions.Exit
            create_issues(str(invalid_csv), "owner/repo", dry_run=False)

    def test_create_issues_invalid_repo_format(self, fixtures_dir):
        """Test handling of invalid repository format."""
        csv_file = str(fixtures_dir / "create_issues.csv")

        with pytest.raises(Exit):  # typer.Exit raises click.exceptions.Exit
            create_issues(csv_file, "invalid-repo-format", dry_run=False)

    def test_create_issues_github_api_error(self, fixtures_dir, mock_github_client):
        """Test handling of GitHub API errors during issue creation."""
        csv_file = str(fixtures_dir / "create_issues.csv")

        # Mock GitHub client to raise an exception
        mock_github_client.create_issue.side_effect = Exception("API Error")

        with patch(
            "cli.common.init_github_client", return_value=mock_github_client
        ), patch("cli.common.validate_token_scopes"), patch(
            "cli.common.validate_repository_access"
        ):
            # Should handle the error gracefully and continue with other issues
            create_issues(csv_file, "owner/repo", dry_run=False)

            # Verify that create_issue was attempted for each row
            assert mock_github_client.create_issue.call_count == 3
