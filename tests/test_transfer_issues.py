import importlib

import pytest
from typer.testing import CliRunner

from ciftt import app
from ciftt.cli.transfer_issues import (
    _load_existing_output_urls,
    _load_transfer_rows,
    _strip_output_columns,
)
from ciftt.utils import is_github_pull_request_url, parse_github_issue_or_pull_url

transfer_module = importlib.import_module("ciftt.cli.transfer_issues")


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


def test_load_existing_output_urls_maps_source_urls_to_target_output(tmp_path):
    output_file = tmp_path / "transferred.csv"
    output_file.write_text(
        "Title,SourceURL,URL\n"
        "Issue one,https://github.com/source/repo/issues/1,https://github.com/target/repo/issues/101\n"
        "Issue two,https://github.com/source/repo/issues/2,https://github.com/other/repo/issues/202\n",
        encoding="utf-8",
    )

    urls = _load_existing_output_urls(str(output_file), "target/repo")

    assert urls == {
        "https://github.com/source/repo/issues/1": "https://github.com/target/repo/issues/101"
    }


def test_load_existing_output_urls_ignores_rows_without_source_url(tmp_path):
    output_file = tmp_path / "transferred.csv"
    output_file.write_text(
        "Title,URL\nIssue one,https://github.com/target/repo/issues/101\n",
        encoding="utf-8",
    )

    urls = _load_existing_output_urls(str(output_file), "target/repo")

    assert urls == {}


def test_strip_output_columns_removes_assignee_and_adds_source_url():
    assert _strip_output_columns(["Title", "Assignee", "URL", "Priority"]) == [
        "Title",
        "URL",
        "Priority",
        "SourceURL",
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

    def update_issue(self, owner, repo, issue_update):
        self.calls.append(
            (
                "update_issue",
                owner,
                repo,
                issue_update.issue_number,
                issue_update.body,
            )
        )
        return {"number": issue_update.issue_number, "title": "patched"}


class FakeDescriptionClient(FakeTransferClient):
    def update_issue(self, owner, repo, issue_update):
        self.calls.append(
            (
                "update_issue",
                owner,
                repo,
                issue_update.issue_number,
                issue_update.body,
            )
        )
        return {"number": issue_update.issue_number, "title": "patched"}


def test_transfer_issues_patches_description_when_description_is_present(
    tmp_path, monkeypatch
):
    input_file = tmp_path / "input.csv"
    output_file = tmp_path / "output.csv"
    input_file.write_text(
        "Title,Description,URL\n"
        "Issue,Line one\\nLine two,https://github.com/source/repo/issues/1\n",
        encoding="utf-8",
    )
    fake_client = FakeDescriptionClient()

    monkeypatch.setattr(
        transfer_module,
        "setup_github_client_for_command",
        lambda required_scopes, repositories: fake_client,
    )

    result = CliRunner().invoke(
        app,
        ["transfer-issues", str(input_file), str(output_file), "target/repo"],
    )

    assert result.exit_code == 0
    assert (
        "update_issue",
        "target",
        "repo",
        101,
        "Line one\nLine two",
    ) in fake_client.calls


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
        "Title,Description,URL,Priority,SourceURL\n"
        "Issue one,Body,https://github.com/target/repo/issues/101,High,https://github.com/source/repo/issues/1\n"
    )
    assert ("transfer_issue", "I_source_1", "R_target") in fake_client.calls


class FakeResumeSourceUrlClient(FakeTransferClient):
    def get_transfer_issue_info(self, owner, repo, issue_number):
        from ciftt.github.data import TransferIssueInfo

        self.calls.append(("get_transfer_issue_info", owner, repo, issue_number))
        if owner == "target":
            return TransferIssueInfo(
                id=f"I_dest_{issue_number}",
                number=issue_number,
                url=f"https://github.com/{owner}/{repo}/issues/{issue_number}",
                state="OPEN",
            )

        return TransferIssueInfo(
            id=f"I_source_{issue_number}",
            number=issue_number,
            url=f"https://github.com/{owner}/{repo}/issues/{issue_number}",
            state="OPEN",
        )

    def transfer_issue(self, issue_id, repository_id):
        from ciftt.github.data import TransferredIssue

        self.calls.append(("transfer_issue", issue_id, repository_id))
        source_number = issue_id.rsplit("_", 1)[1]
        return TransferredIssue(
            id=f"I_dest_20{source_number}",
            number=int(f"20{source_number}"),
            url=f"https://github.com/target/repo/issues/20{source_number}",
        )


def test_transfer_issues_resumes_by_source_url_not_output_position(
    tmp_path, monkeypatch
):
    input_file = tmp_path / "input.csv"
    output_file = tmp_path / "output.csv"
    input_file.write_text(
        "Title,URL\n"
        "One,https://github.com/source/repo/issues/1\n"
        "Two,https://github.com/source/repo/issues/2\n",
        encoding="utf-8",
    )
    output_file.write_text(
        "Title,URL,SourceURL\n"
        "Two,https://github.com/target/repo/issues/202,https://github.com/source/repo/issues/2\n",
        encoding="utf-8",
    )
    fake_client = FakeResumeSourceUrlClient()

    monkeypatch.setattr(
        transfer_module,
        "setup_github_client_for_command",
        lambda required_scopes, repositories: fake_client,
    )

    result = CliRunner().invoke(
        app,
        ["transfer-issues", str(input_file), str(output_file), "target/repo"],
    )

    assert result.exit_code == 0
    assert ("transfer_issue", "I_source_1", "R_target") in fake_client.calls
    assert ("transfer_issue", "I_source_2", "R_target") not in fake_client.calls
    assert output_file.read_text(encoding="utf-8") == (
        "Title,URL,SourceURL\n"
        "One,https://github.com/target/repo/issues/201,https://github.com/source/repo/issues/1\n"
        "Two,https://github.com/target/repo/issues/202,https://github.com/source/repo/issues/2\n"
    )


class FakeSubIssueClient(FakeTransferClient):
    def get_transfer_issue_info(self, owner, repo, issue_number):
        from ciftt.github.data import TransferIssueInfo

        parent_number = None if issue_number == 1 else 1
        return TransferIssueInfo(
            id=f"I_source_{issue_number}",
            number=issue_number,
            url=f"https://github.com/{owner}/{repo}/issues/{issue_number}",
            state="OPEN",
            parent_number=parent_number,
        )

    def transfer_issue(self, issue_id, repository_id):
        from ciftt.github.data import TransferredIssue

        number = 101 if issue_id == "I_source_1" else 102
        return TransferredIssue(
            id=f"I_dest_{number}",
            number=number,
            url=f"https://github.com/target/repo/issues/{number}",
        )

    def add_sub_issue(self, parent_id, child_id):
        self.calls.append(("add_sub_issue", parent_id, child_id))


def test_transfer_issues_relinks_sub_issues(tmp_path, monkeypatch):
    input_file = tmp_path / "input.csv"
    output_file = tmp_path / "output.csv"
    input_file.write_text(
        "Title,URL\n"
        "Parent,https://github.com/source/repo/issues/1\n"
        "Child,https://github.com/source/repo/issues/2\n",
        encoding="utf-8",
    )
    fake_client = FakeSubIssueClient()

    monkeypatch.setattr(
        transfer_module,
        "setup_github_client_for_command",
        lambda required_scopes, repositories: fake_client,
    )

    result = CliRunner().invoke(
        app,
        ["transfer-issues", str(input_file), str(output_file), "target/repo"],
    )

    assert result.exit_code == 0
    assert ("add_sub_issue", "I_dest_101", "I_dest_102") in fake_client.calls


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


class FakeClosedIssueClient(FakeTransferClient):
    def get_transfer_issue_info(self, owner, repo, issue_number):
        from ciftt.github.data import TransferIssueInfo

        self.calls.append(("get_transfer_issue_info", owner, repo, issue_number))
        return TransferIssueInfo(
            id="I_closed_source",
            number=issue_number,
            url=f"https://github.com/{owner}/{repo}/issues/{issue_number}",
            state="CLOSED",
        )

    def comment_issue(self, issue_id, body):
        self.calls.append(("comment_issue", issue_id, body))

    def reopen_issue(self, issue_id):
        self.calls.append(("reopen_issue", issue_id))

    def close_issue(self, issue_id):
        self.calls.append(("close_issue", issue_id))


def test_transfer_issues_reopens_and_recloses_closed_issues(tmp_path, monkeypatch):
    input_file = tmp_path / "input.csv"
    output_file = tmp_path / "output.csv"
    input_file.write_text(
        "Title,URL\nClosed,https://github.com/source/repo/issues/1\n",
        encoding="utf-8",
    )
    fake_client = FakeClosedIssueClient()

    monkeypatch.setattr(
        transfer_module,
        "setup_github_client_for_command",
        lambda required_scopes, repositories: fake_client,
    )

    result = CliRunner().invoke(
        app,
        ["transfer-issues", str(input_file), str(output_file), "target/repo"],
    )

    assert result.exit_code == 0
    assert fake_client.calls[2][0] == "comment_issue"
    assert fake_client.calls[3] == ("reopen_issue", "I_closed_source")
    assert ("close_issue", "I_dest_101") in fake_client.calls


class FakeClosedIssueTransferFailureClient(FakeClosedIssueClient):
    def transfer_issue(self, issue_id, repository_id):
        self.calls.append(("transfer_issue", issue_id, repository_id))
        raise ValueError("transfer failed")


def test_transfer_issues_recloses_source_when_transfer_fails_after_reopen(
    tmp_path, monkeypatch
):
    input_file = tmp_path / "input.csv"
    output_file = tmp_path / "output.csv"
    input_file.write_text(
        "Title,URL\nClosed,https://github.com/source/repo/issues/1\n",
        encoding="utf-8",
    )
    fake_client = FakeClosedIssueTransferFailureClient()

    monkeypatch.setattr(
        transfer_module,
        "setup_github_client_for_command",
        lambda required_scopes, repositories: fake_client,
    )

    result = CliRunner().invoke(
        app,
        ["transfer-issues", str(input_file), str(output_file), "target/repo"],
    )

    assert result.exit_code == 1
    assert fake_client.calls[3] == ("reopen_issue", "I_closed_source")
    assert ("close_issue", "I_closed_source") in fake_client.calls


def test_transfer_issues_dry_run_does_not_mutate_existing_output_file(
    tmp_path, monkeypatch
):
    input_file = tmp_path / "input.csv"
    output_file = tmp_path / "output.csv"
    input_file.write_text(
        "Title,URL\nOne,https://github.com/source/repo/issues/1\n",
        encoding="utf-8",
    )
    existing_output = "Title,URL\nExisting,https://github.com/target/repo/issues/99\n"
    output_file.write_text(existing_output, encoding="utf-8")
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
            "--dry-run",
        ],
    )

    assert result.exit_code == 0
    assert output_file.read_text(encoding="utf-8") == existing_output
    assert ("transfer_issue", "I_source_1", "R_target") not in fake_client.calls


def test_transfer_issues_dry_run_does_not_patch_resumed_description(
    tmp_path, monkeypatch
):
    input_file = tmp_path / "input.csv"
    output_file = tmp_path / "output.csv"
    input_file.write_text(
        "Title,Description,URL\n"
        "One,Updated body,https://github.com/source/repo/issues/1\n",
        encoding="utf-8",
    )
    existing_output = (
        "Title,Description,URL\nOne,Old body,https://github.com/target/repo/issues/99\n"
    )
    output_file.write_text(existing_output, encoding="utf-8")
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
            "--dry-run",
        ],
    )

    assert result.exit_code == 0
    assert output_file.read_text(encoding="utf-8") == existing_output
    assert not any(call[0] == "update_issue" for call in fake_client.calls)


class FakeResumeRelinkClient(FakeSubIssueClient):
    def get_transfer_issue_info(self, owner, repo, issue_number):
        from ciftt.github.data import TransferIssueInfo

        if owner == "target":
            return TransferIssueInfo(
                id="I_existing_parent",
                number=101,
                url="https://github.com/target/repo/issues/101",
                state="OPEN",
            )

        return TransferIssueInfo(
            id=f"I_source_{issue_number}",
            number=issue_number,
            url=f"https://github.com/{owner}/{repo}/issues/{issue_number}",
            state="OPEN",
            parent_number=1 if issue_number == 2 else None,
        )

    def transfer_issue(self, issue_id, repository_id):
        from ciftt.github.data import TransferredIssue

        return TransferredIssue(
            id="I_new_child",
            number=102,
            url="https://github.com/target/repo/issues/102",
        )


def test_transfer_issues_can_relink_to_parent_from_existing_output(
    tmp_path, monkeypatch
):
    input_file = tmp_path / "input.csv"
    output_file = tmp_path / "output.csv"
    input_file.write_text(
        "Title,URL\n"
        "Parent,https://github.com/source/repo/issues/1\n"
        "Child,https://github.com/source/repo/issues/2\n",
        encoding="utf-8",
    )
    output_file.write_text(
        "Title,URL,SourceURL\n"
        "Parent,https://github.com/target/repo/issues/101,https://github.com/source/repo/issues/1\n",
        encoding="utf-8",
    )
    fake_client = FakeResumeRelinkClient()

    monkeypatch.setattr(
        transfer_module,
        "setup_github_client_for_command",
        lambda required_scopes, repositories: fake_client,
    )

    result = CliRunner().invoke(
        app,
        ["transfer-issues", str(input_file), str(output_file), "target/repo"],
    )

    assert result.exit_code == 0
    assert ("add_sub_issue", "I_existing_parent", "I_new_child") in fake_client.calls
