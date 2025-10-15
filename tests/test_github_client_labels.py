import pytest
from unittest.mock import Mock, patch

from github.client import GitHubClient


@pytest.fixture
def mock_github_client():
    """Create a GitHubClient instance with mocked requests."""
    return GitHubClient(api_key="test_token", url="https://api.github.com/")


def test_add_labels_to_issue_uses_post(mock_github_client):
    """Test that add_labels_to_issue uses POST method to append labels."""
    with patch.object(mock_github_client, "_post_request") as mock_post:
        mock_post.return_value = {
            "number": 123,
            "labels": [
                {"name": "bug"},
                {"name": "enhancement"},
                {"name": "ui"},
            ],
        }

        result = mock_github_client.add_labels_to_issue(
            "owner", "repo", 123, ["enhancement", "ui"]
        )

        mock_post.assert_called_once_with(
            "repos/owner/repo/issues/123/labels", {"labels": ["enhancement", "ui"]}
        )
        assert result["number"] == 123
        assert len(result["labels"]) == 3


def test_add_labels_to_issue_with_empty_list(mock_github_client):
    """Test that add_labels_to_issue handles empty label list."""
    with patch.object(mock_github_client, "_post_request") as mock_post:
        mock_post.return_value = {"number": 123, "labels": []}

        result = mock_github_client.add_labels_to_issue("owner", "repo", 123, [])

        mock_post.assert_called_once_with(
            "repos/owner/repo/issues/123/labels", {"labels": []}
        )
        assert result["number"] == 123


def test_update_issue_with_labels_uses_patch(mock_github_client):
    """Test that update_issue uses PATCH method which replaces labels."""
    from github.data import UpdatedIssue

    with patch.object(mock_github_client, "_patch_request") as mock_patch:
        mock_patch.return_value = {
            "number": 123,
            "title": "Updated Issue",
            "labels": [{"name": "new-label"}],
        }

        issue_update = UpdatedIssue(
            url="https://github.com/owner/repo/issues/123",
            title="Updated Issue",
            labels=["new-label"],
        )

        result = mock_github_client.update_issue("owner", "repo", issue_update)

        mock_patch.assert_called_once()
        endpoint, data = mock_patch.call_args[0]
        assert endpoint == "repos/owner/repo/issues/123"
        assert "labels" in data
        assert data["labels"] == ["new-label"]


def test_add_labels_endpoint_format(mock_github_client):
    """Test that the endpoint for adding labels is correctly formatted."""
    with patch.object(mock_github_client, "_post_request") as mock_post:
        mock_post.return_value = {"number": 456, "labels": [{"name": "test"}]}

        mock_github_client.add_labels_to_issue(
            "test-owner", "test-repo", 456, ["test"]
        )

        expected_endpoint = "repos/test-owner/test-repo/issues/456/labels"
        mock_post.assert_called_once()
        actual_endpoint = mock_post.call_args[0][0]
        assert actual_endpoint == expected_endpoint
