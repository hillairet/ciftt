import pytest

from utils import (
    extract_issue_number,
    extract_repo_from_issue_url,
    parse_github_project_identifier,
    parse_issue_numbers,
    parse_repo,
    safe_decode,
)


class TestParseRepo:
    def test_valid_repo_format(self):
        owner, repo_name = parse_repo("owner/repo")
        assert owner == "owner"
        assert repo_name == "repo"

    def test_invalid_repo_format_no_slash(self):
        with pytest.raises(ValueError, match="Repository must be in format"):
            parse_repo("owner-repo")

    def test_invalid_repo_format_multiple_slashes(self):
        with pytest.raises(ValueError, match="Repository must be in format"):
            parse_repo("owner/repo/extra")


class TestExtractIssueNumber:
    def test_valid_github_issue_url(self):
        url = "https://github.com/owner/repo/issues/123"
        assert extract_issue_number(url) == 123

    def test_url_with_trailing_content(self):
        url = "https://github.com/owner/repo/issues/456/comments"
        assert extract_issue_number(url) is None

    def test_empty_url(self):
        assert extract_issue_number("") is None

    def test_none_url(self):
        assert extract_issue_number(None) is None

    def test_non_string_url(self):
        assert extract_issue_number(123) is None

    def test_url_without_issues_path(self):
        url = "https://github.com/owner/repo/pull/123"
        assert extract_issue_number(url) is None


class TestSafeDecode:
    def test_decode_newline_escape(self):
        result = safe_decode("Line 1\\nLine 2")
        assert result == "Line 1\nLine 2"

    def test_decode_tab_escape(self):
        result = safe_decode("Column1\\tColumn2")
        assert result == "Column1\tColumn2"

    def test_decode_return_escape(self):
        result = safe_decode("Line\\r\\n")
        assert result == "Line\r\n"

    def test_invalid_unicode_returns_original(self):
        result = safe_decode("Invalid\\xGG")
        assert result == "Invalid\\xGG"

    def test_non_string_returns_original(self):
        assert safe_decode(123) == 123
        assert safe_decode(None) is None
        assert safe_decode([1, 2]) == [1, 2]


class TestParseIssueNumbers:
    def test_single_issue_number(self):
        result = parse_issue_numbers("123")
        assert result == [123]

    def test_multiple_issue_numbers(self):
        result = parse_issue_numbers("1,2,3")
        assert result == [1, 2, 3]

    def test_issue_range(self):
        result = parse_issue_numbers("1-5")
        assert result == [1, 2, 3, 4, 5]

    def test_mixed_numbers_and_ranges(self):
        result = parse_issue_numbers("1,3-5,8")
        assert result == [1, 3, 4, 5, 8]

    def test_whitespace_handling(self):
        result = parse_issue_numbers(" 1 , 2 , 3 ")
        assert result == [1, 2, 3]

    def test_empty_string_returns_none(self):
        result = parse_issue_numbers("")
        assert result is None

    def test_invalid_issue_number(self):
        with pytest.raises(ValueError, match="Invalid issue number: abc"):
            parse_issue_numbers("abc")

    def test_invalid_range_format(self):
        with pytest.raises(ValueError, match="Invalid issue range: 1-a"):
            parse_issue_numbers("1-a")

    def test_invalid_range_non_numeric(self):
        with pytest.raises(ValueError, match="Invalid issue range: a-b"):
            parse_issue_numbers("a-b")


class TestParseGithubProjectIdentifier:
    def test_full_user_url(self):
        url = "https://github.com/users/owner/projects/123"
        owner, project_number = parse_github_project_identifier(url)
        assert owner == "owner"
        assert project_number == "123"

    def test_full_org_url(self):
        url = "https://github.com/orgs/myorg/projects/456"
        owner, project_number = parse_github_project_identifier(url)
        assert owner == "myorg"
        assert project_number == "456"

    def test_short_format(self):
        identifier = "owner/projects/123"
        owner, project_number = parse_github_project_identifier(identifier)
        assert owner == "owner"
        assert project_number == "123"

    def test_shortest_format(self):
        identifier = "owner/123"
        owner, project_number = parse_github_project_identifier(identifier)
        assert owner == "owner"
        assert project_number == "123"

    def test_invalid_format_raises_error(self):
        with pytest.raises(ValueError, match="Invalid project identifier format"):
            parse_github_project_identifier("invalid-format")

    def test_invalid_format_with_helpful_message(self):
        with pytest.raises(ValueError) as exc_info:
            parse_github_project_identifier("wrong")

        assert "Supported formats:" in str(exc_info.value)
        assert "users/owner/projects/123" in str(exc_info.value)


class TestExtractRepoFromIssueUrl:
    def test_valid_issue_url(self):
        url = "https://github.com/owner/repo/issues/123"
        owner, repo_name = extract_repo_from_issue_url(url)
        assert owner == "owner"
        assert repo_name == "repo"

    def test_different_issue_number(self):
        url = "https://github.com/myorg/myrepo/issues/999"
        owner, repo_name = extract_repo_from_issue_url(url)
        assert owner == "myorg"
        assert repo_name == "myrepo"

    def test_invalid_url_format(self):
        with pytest.raises(ValueError, match="Invalid GitHub issue URL format"):
            extract_repo_from_issue_url("https://github.com/owner/repo")

    def test_pull_request_url_invalid(self):
        url = "https://github.com/owner/repo/pull/123"
        with pytest.raises(ValueError, match="Invalid GitHub issue URL format"):
            extract_repo_from_issue_url(url)

    def test_url_with_trailing_path(self):
        url = "https://github.com/owner/repo/issues/123/comments"
        owner, repo_name = extract_repo_from_issue_url(url)
        assert owner == "owner"
        assert repo_name == "repo"
