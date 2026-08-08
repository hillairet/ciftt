from ciftt.cli.project_fields import fetch_github_project_fields


def test_fetch_github_project_fields_reports_periodic_progress(capsys):
    issue_numbers = list(range(1, 53))
    issues_data = [{"number": number} for number in issue_numbers]

    class FakeGitHubClient:
        def get_project_fields_for_issues(
            self, owner, repo, issue_numbers, field_names, progress_callback=None
        ):
            for index, issue_number in enumerate(issue_numbers, start=1):
                if progress_callback:
                    progress_callback(index, len(issue_numbers), issue_number)
            return {issue_number: {"Status": "Todo"} for issue_number in issue_numbers}

    project_field_data, field_names = fetch_github_project_fields(
        FakeGitHubClient(),
        "owner",
        "repo",
        issues_data,
        "Status",
    )

    captured = capsys.readouterr()

    assert field_names == ["Status"]
    assert len(project_field_data) == 52
    assert "🔍 Fetching project fields for 52 issues: Status" in captured.out
    assert "⏳ Fetched project fields for 1/52 issues" in captured.out
    assert "⏳ Fetched project fields for 25/52 issues" in captured.out
    assert "⏳ Fetched project fields for 50/52 issues" in captured.out
    assert "⏳ Fetched project fields for 52/52 issues" in captured.out
