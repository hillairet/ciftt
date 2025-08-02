from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from click.exceptions import Exit

from cli.update_issues import update_issues


class TestUpdateIssuesIntegration:
    """Integration tests for the update_issues command."""

    def test_update_issues_success(self, fixtures_dir, mock_github_client):
        """Test successful updating of issues from CSV."""
        csv_file = str(fixtures_dir / "update_issues.csv")

        with patch(
            "cli.update_issues.init_github_client", return_value=mock_github_client
        ), patch("cli.update_issues.validate_token_scopes"), patch(
            "cli.update_issues.validate_repository_access"
        ):

            # This should not raise any exceptions
            update_issues(csv_file, "owner/repo", dry_run=False)

            # Verify that update_issue was called for each row in the CSV
            assert mock_github_client.update_issue.call_count == 3

    def test_update_issues_dry_run(self, fixtures_dir, capsys):
        """Test dry run mode for update issues."""
        csv_file = str(fixtures_dir / "update_issues.csv")

        # Dry run should not require GitHub client
        update_issues(csv_file, "owner/repo", dry_run=True)

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
            update_issues(str(invalid_csv), "owner/repo", dry_run=False)

    def test_update_issues_invalid_repo_format(self, fixtures_dir):
        """Test handling of invalid repository format."""
        csv_file = str(fixtures_dir / "update_issues.csv")

        with pytest.raises(Exit):  # typer.Exit raises click.exceptions.Exit
            update_issues(csv_file, "invalid-repo-format", dry_run=False)

    def test_update_issues_github_api_error(self, fixtures_dir, mock_github_client):
        """Test handling of GitHub API errors during issue updates."""
        csv_file = str(fixtures_dir / "update_issues.csv")

        # Mock GitHub client to raise an exception
        mock_github_client.update_issue.side_effect = Exception("API Error")

        with patch(
            "cli.update_issues.init_github_client", return_value=mock_github_client
        ), patch("cli.update_issues.validate_token_scopes"), patch(
            "cli.update_issues.validate_repository_access"
        ):

            # Should handle the error gracefully and continue with other issues
            update_issues(csv_file, "owner/repo", dry_run=False)

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
            update_issues(str(invalid_csv), "owner/repo", dry_run=False)
