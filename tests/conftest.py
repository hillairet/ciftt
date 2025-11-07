from pathlib import Path
from unittest.mock import Mock

import pytest

from ciftt.github.data import ProjectFieldUpdateResult


@pytest.fixture
def mock_github_client():
    """Mock GitHub client for integration tests."""
    client = Mock()

    # Mock successful API responses
    client.create_issue.return_value = {
        "number": 123,
        "title": "Test Issue",
        "html_url": "https://github.com/owner/repo/issues/123",
    }

    client.update_issue.return_value = {
        "number": 123,
        "title": "Updated Test Issue",
        "html_url": "https://github.com/owner/repo/issues/123",
    }

    client.update_issue_project_fields.return_value = ProjectFieldUpdateResult()

    client._get_request.return_value = {"permissions": {"push": True}}
    client._request.return_value = ({}, {"X-OAuth-Scopes": "repo"})

    return client


@pytest.fixture
def fixtures_dir():
    """Path to test fixtures directory."""
    return Path(__file__).parent / "integration" / "fixtures"
