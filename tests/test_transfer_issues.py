import pytest
from typer.testing import CliRunner

from ciftt import app
from ciftt.cli import transfer_issues as transfer_module
from ciftt.cli.transfer_issues import (
    _load_existing_output_urls,
    _load_transfer_rows,
    _strip_output_columns,
)
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


def test_load_transfer_rows_reads_valid_issue_rows_and_skips_pulls(tmp_path):
    input_file = tmp_path / "input.csv"
    input_file.write_text(
        "Title,Description,URL\n"
        "Issue one,Body,https://github.com/source/repo/issues/1\n"
        "Pull request,Body,https://github.com/source/repo/pull/2\n",
        encoding="utf-8",
    )

    headers, rows, delimiter = _load_transfer_rows(str(input_file))

    assert headers == ["Title", "Description", "URL"]
    assert delimiter == ","
    assert len(rows) == 1
    assert rows[0].source_url == "https://github.com/source/repo/issues/1"
    assert rows[0].source_parts.number == 1


def test_load_transfer_rows_requires_url_column(tmp_path):
    input_file = tmp_path / "input.csv"
    input_file.write_text("Title\nMissing URL\n", encoding="utf-8")

    with pytest.raises(ValueError, match="URL column is required"):
        _load_transfer_rows(str(input_file))


def test_load_existing_output_urls_maps_input_to_target_output_by_row(tmp_path):
    output_file = tmp_path / "transferred.csv"
    output_file.write_text(
        "Title,URL\n"
        "Issue one,https://github.com/target/repo/issues/101\n"
        "Issue two,https://github.com/other/repo/issues/202\n",
        encoding="utf-8",
    )

    urls = _load_existing_output_urls(str(output_file), "target/repo")

    assert urls == {"1": "https://github.com/target/repo/issues/101"}


def test_strip_output_columns_removes_assignee_only():
    assert _strip_output_columns(["Title", "Assignee", "URL", "Priority"]) == [
        "Title",
        "URL",
        "Priority",
    ]


class FakeTransferClient:
    def __init__(self):
        self.calls = []

    def get_repository_node_id(self, owner, repo):
        self.calls.append(("get_repository_node_id", owner, repo))
        return "R_target"

    def get_transfer_issue_info(self, owner, repo, issue_number):
        from ciftt.github.data import TransferIssueInfo

        self.calls.append(("get_transfer_issue_info", owner, repo, issue_number))
        return TransferIssueInfo(
            id=f"I_source_{issue_number}",
            number=issue_number,
            url=f"https://github.com/{owner}/{repo}/issues/{issue_number}",
            state="OPEN",
        )

    def transfer_issue(self, issue_id, repository_id):
        from ciftt.github.data import TransferredIssue

        self.calls.append(("transfer_issue", issue_id, repository_id))
        return TransferredIssue(
            id="I_dest_101",
            number=101,
            url="https://github.com/target/repo/issues/101",
        )


def test_transfer_issues_command_writes_output_with_destination_url(
    tmp_path, monkeypatch
):
    input_file = tmp_path / "input.csv"
    output_file = tmp_path / "output.csv"
    input_file.write_text(
        "Title,Description,Assignee,URL,Priority\n"
        "Issue one,Body,octocat,https://github.com/source/repo/issues/1,High\n",
        encoding="utf-8",
    )
    fake_client = FakeTransferClient()

    monkeypatch.setattr(
        transfer_module,
        "setup_github_client_for_command",
        lambda required_scopes, repositories: fake_client,
    )

    result = CliRunner().invoke(
        app,
        [
            "transfer-issues",
            str(input_file),
            str(output_file),
            "target/repo",
        ],
    )

    assert result.exit_code == 0
    assert output_file.read_text(encoding="utf-8") == (
        "Title,Description,URL,Priority\n"
        "Issue one,Body,https://github.com/target/repo/issues/101,High\n"
    )
    assert ("transfer_issue", "I_source_1", "R_target") in fake_client.calls


def test_transfer_issues_command_honors_limit(tmp_path, monkeypatch):
    input_file = tmp_path / "input.csv"
    output_file = tmp_path / "output.csv"
    input_file.write_text(
        "Title,URL\n"
        "One,https://github.com/source/repo/issues/1\n"
        "Two,https://github.com/source/repo/issues/2\n",
        encoding="utf-8",
    )
    fake_client = FakeTransferClient()

    monkeypatch.setattr(
        transfer_module,
        "setup_github_client_for_command",
        lambda required_scopes, repositories: fake_client,
    )

    result = CliRunner().invoke(
        app,
        [
            "transfer-issues",
            str(input_file),
            str(output_file),
            "target/repo",
            "--limit",
            "1",
        ],
    )

    assert result.exit_code == 0
    assert output_file.read_text(encoding="utf-8").count("target/repo") == 1
