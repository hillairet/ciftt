from unittest.mock import Mock, patch

import pytest
from click.exceptions import Exit

from ciftt.cli.update_issues import update_issues
from ciftt.github.data import ProjectFieldUpdateResult, ProjectInfo


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
            type="user",
        )

        with patch(
            "ciftt.cli.common.init_github_client", return_value=mock_github_client
        ), patch("ciftt.cli.common.validate_token_scopes"), patch(
            "ciftt.cli.common.validate_repository_access"
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
            type="user",
        )

        # Mock GitHub client to raise an exception
        mock_github_client.update_issue.side_effect = Exception("API Error")

        with patch(
            "ciftt.cli.common.init_github_client", return_value=mock_github_client
        ), patch("ciftt.cli.common.validate_token_scopes"), patch(
            "ciftt.cli.common.validate_repository_access"
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

        with patch("ciftt.cli.common.init_github_client"), patch(
            "ciftt.cli.common.validate_token_scopes"
        ), patch("ciftt.cli.common.validate_repository_access"):
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
            type="user",
        )

        # Mock project field definitions
        mock_github_client.get_project_field_definitions.return_value = {
            "Priority": {"name": "Priority", "dataType": "SINGLE_SELECT"},
            "Status": {"name": "Status", "dataType": "SINGLE_SELECT"},
        }

        # Mock project field update method
        mock_github_client.update_issue_project_fields.return_value = (
            ProjectFieldUpdateResult(
                updated_fields={"Priority": "High", "Status": "In Progress"}, errors={}
            )
        )

        with patch(
            "ciftt.cli.common.init_github_client", return_value=mock_github_client
        ), patch("ciftt.cli.common.validate_token_scopes"), patch(
            "ciftt.cli.common.validate_repository_access"
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

    def test_update_issues_without_project_no_fields(
        self, tmp_path, mock_github_client
    ):
        """Test updating issues without project option when CSV has no project fields."""
        csv_no_fields = tmp_path / "no_project_fields.csv"
        csv_no_fields.write_text(
            "Title,Description,URL\n"
            "Updated Title,Updated description,https://github.com/owner/repo/issues/123\n"
        )

        with patch(
            "ciftt.cli.common.init_github_client", return_value=mock_github_client
        ), patch("ciftt.cli.common.validate_token_scopes"), patch(
            "ciftt.cli.common.validate_repository_access"
        ):
            update_issues(str(csv_no_fields), project=None, dry_run=False)

            assert mock_github_client.update_issue.call_count == 1
            mock_github_client.validate_project_exists.assert_not_called()
            mock_github_client.update_issue_project_fields.assert_not_called()

    def test_update_issues_without_project_with_fields_warning(
        self, tmp_path, mock_github_client, capsys
    ):
        """Test warning shown when CSV has project fields but no project option provided."""
        csv_with_fields = tmp_path / "with_project_fields.csv"
        csv_with_fields.write_text(
            "Title,URL,Priority,Status\n"
            "Test Issue,https://github.com/owner/repo/issues/123,High,Todo\n"
        )

        with patch(
            "ciftt.cli.common.init_github_client", return_value=mock_github_client
        ), patch("ciftt.cli.common.validate_token_scopes"), patch(
            "ciftt.cli.common.validate_repository_access"
        ):
            update_issues(str(csv_with_fields), project=None, dry_run=False)

            captured = capsys.readouterr()
            assert (
                "⚠️  Warning: Project fields detected but no project provided"
                in captured.out
            )
            assert "Priority, Status" in captured.out
            assert "💡 Tip: Use --project option" in captured.out

            assert mock_github_client.update_issue.call_count == 1
            mock_github_client.validate_project_exists.assert_not_called()
            mock_github_client.update_issue_project_fields.assert_not_called()

    def test_update_issues_scope_requirements_without_project(self, tmp_path, capsys):
        """Test that only 'repo' scope is required when project is not provided."""
        csv_file = tmp_path / "simple.csv"
        csv_file.write_text(
            "Title,Description,URL\n"
            "Test,Description,https://github.com/owner/repo/issues/123\n"
        )

        mock_client = Mock()
        mock_client.update_issue.return_value = {
            "number": 123,
            "title": "Test",
            "html_url": "https://github.com/owner/repo/issues/123",
        }

        with patch(
            "ciftt.cli.common.init_github_client", return_value=mock_client
        ), patch("ciftt.cli.common.validate_token_scopes") as mock_validate, patch(
            "ciftt.cli.common.validate_repository_access"
        ):
            update_issues(str(csv_file), project=None, dry_run=False)

            mock_validate.assert_called_once_with(mock_client, ["repo"])

    def test_update_issues_scope_requirements_with_project(
        self, tmp_path, mock_github_client
    ):
        """Test that both 'repo' and 'project' scopes are required when project is provided."""
        csv_file = tmp_path / "simple.csv"
        csv_file.write_text(
            "Title,Description,URL\n"
            "Test,Description,https://github.com/owner/repo/issues/123\n"
        )

        mock_github_client.validate_project_exists.return_value = ProjectInfo(
            id="test-id",
            title="Test Project",
            number=123,
            url="https://github.com/users/owner/projects/123",
            owner="owner",
            type="user",
        )

        mock_github_client.get_project_field_definitions.return_value = {}

        with patch(
            "ciftt.cli.common.init_github_client", return_value=mock_github_client
        ), patch("ciftt.cli.common.validate_token_scopes") as mock_validate, patch(
            "ciftt.cli.common.validate_repository_access"
        ):
            update_issues(str(csv_file), project="owner/123", dry_run=False)

            mock_validate.assert_called_once_with(
                mock_github_client, ["repo", "project"]
            )

    def test_update_issues_dry_run_without_project(self, tmp_path, capsys):
        """Test dry run mode without project option."""
        csv_file = tmp_path / "simple.csv"
        csv_file.write_text(
            "Title,Description,URL\n"
            "Updated Title,Updated desc,https://github.com/owner/repo/issues/456\n"
        )

        update_issues(str(csv_file), project=None, dry_run=True)

        captured = capsys.readouterr()
        assert "DRY RUN MODE" in captured.out
        assert "Would update issue #456" in captured.out
        assert "📋 No project fields detected - updating issues only" in captured.out

    def test_update_issues_dry_run_with_project_fields_no_project(
        self, tmp_path, capsys
    ):
        """Test dry run shows warning when project fields present but no project."""
        csv_file = tmp_path / "with_fields.csv"
        csv_file.write_text(
            "Title,URL,Status\n"
            "Test,https://github.com/owner/repo/issues/789,In Progress\n"
        )

        update_issues(str(csv_file), project=None, dry_run=True)

        captured = capsys.readouterr()
        assert "DRY RUN MODE" in captured.out
        assert "📊 Detected project fields: Status" in captured.out
        assert (
            "⚠️  Warning: Project fields detected but no project provided"
            in captured.out
        )
        assert "Status" in captured.out

    def test_update_issues_with_state_reason(
        self, tmp_path, mock_github_client
    ):
        """Test that StateReason column is properly sent to GitHub API."""
        csv_file = tmp_path / "state_reason.csv"
        csv_file.write_text(
            "Title,State,StateReason,URL\n"
            "Issue to close,closed,not_planned,https://github.com/owner/repo/issues/100\n"
            "Duplicate issue,closed,duplicate,https://github.com/owner/repo/issues/101\n"
        )

        with patch(
            "ciftt.cli.common.init_github_client", return_value=mock_github_client
        ), patch("ciftt.cli.common.validate_token_scopes"), patch(
            "ciftt.cli.common.validate_repository_access"
        ):
            update_issues(str(csv_file), project=None, dry_run=False)

            assert mock_github_client.update_issue.call_count == 2

            first_call_args = mock_github_client.update_issue.call_args_list[0]
            issue_1 = first_call_args[0][2]
            assert issue_1.state == "closed"
            assert issue_1.state_reason == "not_planned"

            second_call_args = mock_github_client.update_issue.call_args_list[1]
            issue_2 = second_call_args[0][2]
            assert issue_2.state == "closed"
            assert issue_2.state_reason == "duplicate"

    def test_update_issues_without_project_validates_all_fields(
        self, tmp_path, mock_github_client
    ):
        """Test that all issue fields are correctly passed to API when no project provided."""
        csv_file = tmp_path / "all_fields.csv"
        csv_file.write_text(
            "Title,Description,Labels,Assignees,State,StateReason,URL\n"
            "Updated Title,New description,bug,user1,closed,not_planned,https://github.com/owner/repo/issues/100\n"
        )

        with patch(
            "ciftt.cli.common.init_github_client", return_value=mock_github_client
        ), patch("ciftt.cli.common.validate_token_scopes"), patch(
            "ciftt.cli.common.validate_repository_access"
        ):
            update_issues(str(csv_file), project=None, dry_run=False)

            assert mock_github_client.update_issue.call_count == 1

            call_args = mock_github_client.update_issue.call_args_list[0]
            owner, repo, issue = call_args[0]

            assert owner == "owner"
            assert repo == "repo"
            assert issue.title == "Updated Title"
            assert issue.body == "New description"
            assert issue.labels == ["bug"]
            assert issue.assignees == ["user1"]
            assert issue.state == "closed"
            assert issue.state_reason == "not_planned"
            assert issue.issue_number == 100
