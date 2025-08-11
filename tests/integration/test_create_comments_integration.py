from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from click.exceptions import Exit

from cli.create_comments import create_comments


class TestCreateCommentsIntegration:
    """Integration tests for the create_comments command."""

    def test_create_comments_success(self, fixtures_dir, mock_github_client):
        """Test successful creation of comments from CSV."""
        csv_file = str(fixtures_dir / "create_comments.csv")

        with patch(
            "cli.common.init_github_client", return_value=mock_github_client
        ), patch("cli.common.validate_token_scopes"), patch(
            "cli.common.validate_repository_access"
        ):

            create_comments(csv_file, dry_run=False)

            # Verify that create_issue_comment was called for each row in the CSV
            assert mock_github_client.create_issue_comment.call_count == 3

            # Verify the calls were made with correct parameters
            calls = mock_github_client.create_issue_comment.call_args_list

            # First call with attribution
            assert calls[0][0][:3] == ("owner", "repo", 123)
            comment_body = calls[0][0][3]
            assert "This was originally reported in JIRA-456" in comment_body
            assert "*Originally by: john.doe | Date: 2024-01-15*" in comment_body

            # Second call with attribution
            assert calls[1][0][:3] == ("owner", "repo", 124)

            # Third call different repo, no attribution
            assert calls[2][0][:3] == ("another", "repo", 42)

    def test_create_comments_dry_run(self, fixtures_dir, capsys):
        """Test dry run mode for create comments."""
        csv_file = str(fixtures_dir / "create_comments.csv")

        create_comments(csv_file, dry_run=True)

        captured = capsys.readouterr()
        assert "🧪 Dry run mode" in captured.out
        assert "Would create comment on owner/repo#123" in captured.out
        assert "Would create comment on owner/repo#124" in captured.out
        assert "Would create comment on another/repo#42" in captured.out

    def test_create_comments_missing_url_column(self, tmp_path):
        """Test handling of CSV missing URL column."""
        invalid_csv = tmp_path / "invalid.csv"
        invalid_csv.write_text("Comment,Author\nTest comment,author")

        with pytest.raises(Exit):
            create_comments(str(invalid_csv), dry_run=False)

    def test_create_comments_missing_comment_column(self, tmp_path):
        """Test handling of CSV missing Comment column."""
        invalid_csv = tmp_path / "invalid.csv"
        invalid_csv.write_text(
            "URL,Author\nhttps://github.com/owner/repo/issues/123,author"
        )

        with pytest.raises(Exit):
            create_comments(str(invalid_csv), dry_run=False)

    def test_create_comments_empty_url_values(self, tmp_path):
        """Test handling of empty URL values."""
        invalid_csv = tmp_path / "invalid.csv"
        invalid_csv.write_text(
            "URL,Comment\n,Test comment\nhttps://github.com/owner/repo/issues/123,Another comment"
        )

        with pytest.raises(Exit):
            create_comments(str(invalid_csv), dry_run=False)

    def test_create_comments_invalid_url_format(self, tmp_path, capsys):
        """Test handling of invalid URL format in dry run."""
        invalid_csv = tmp_path / "invalid.csv"
        invalid_csv.write_text("URL,Comment\ninvalid-url,Test comment")

        create_comments(str(invalid_csv), dry_run=True)

        captured = capsys.readouterr()
        assert "❌ Row 1: Invalid URL format" in captured.out

    def test_create_comments_github_api_error(
        self, fixtures_dir, mock_github_client, capsys
    ):
        """Test handling of GitHub API errors during comment creation."""
        csv_file = str(fixtures_dir / "create_comments.csv")

        # Mock first call to succeed, second to fail
        mock_github_client.create_issue_comment.side_effect = [
            {"id": 12345},
            Exception("API Error"),
            {"id": 12346},
        ]

        with patch(
            "cli.common.init_github_client", return_value=mock_github_client
        ), patch("cli.common.validate_token_scopes"), patch(
            "cli.common.validate_repository_access"
        ):

            create_comments(csv_file, dry_run=False)

            # Verify that create_issue_comment was attempted for each row
            assert mock_github_client.create_issue_comment.call_count == 3

            # Check that error was logged but execution continued
            captured = capsys.readouterr()
            assert "✅ Created comment 12345" in captured.out
            assert "❌ Row 2: Failed to create comment" in captured.out
            assert "✅ Created comment 12346" in captured.out
            assert "📊 Summary: 2 comments created, 1 failed" in captured.out
