import pytest

from ciftt.utils import is_github_pull_request_url, parse_github_issue_or_pull_url


def test_parse_github_issue_url_returns_parts():
    parts = parse_github_issue_or_pull_url(
        "https://github.com/source-org/source-repo/issues/42"
    )

    assert parts.owner == "source-org"
    assert parts.repo == "source-repo"
    assert parts.number == 42
    assert parts.kind == "issue"


def test_parse_github_pull_url_returns_parts():
    parts = parse_github_issue_or_pull_url(
        "https://github.com/source-org/source-repo/pull/7"
    )

    assert parts.owner == "source-org"
    assert parts.repo == "source-repo"
    assert parts.number == 7
    assert parts.kind == "pull"


def test_is_github_pull_request_url_detects_pull_urls():
    assert is_github_pull_request_url(
        "https://github.com/source-org/source-repo/pull/7"
    )
    assert not is_github_pull_request_url(
        "https://github.com/source-org/source-repo/issues/7"
    )


def test_parse_github_issue_or_pull_url_rejects_invalid_url():
    with pytest.raises(ValueError, match="Invalid GitHub issue or pull request URL"):
        parse_github_issue_or_pull_url("https://example.com/not/github")
