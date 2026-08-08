from ciftt.cli.issues import fetch_issues_from_github


def test_fetch_all_issues_reports_page_progress(capsys):
    class FakeGitHubClient:
        def get_all_issues(self, owner, repo, state="open", progress_callback=None):
            if progress_callback:
                progress_callback(1, 100, 100)
                progress_callback(2, 150, 50)
            return [{"number": number} for number in range(1, 151)]

    issues = fetch_issues_from_github(
        FakeGitHubClient(), "owner", "repo", [], all_issues=False
    )

    captured = capsys.readouterr()

    assert len(issues) == 150
    assert "🔍 Fetching open issues from repository..." in captured.out
    assert "⏳ Fetched 100 issues across 1 page" in captured.out
    assert "⏳ Fetched 150 issues across 2 pages" in captured.out
    assert "📋 Found 150 issues" in captured.out


def test_fetch_specific_issues_reports_periodic_progress(capsys):
    issue_numbers = list(range(1, 53))

    class FakeGitHubClient:
        def get_issues_by_numbers(
            self, owner, repo, issue_numbers, progress_callback=None
        ):
            for index, issue_number in enumerate(issue_numbers, start=1):
                if progress_callback:
                    progress_callback(index, len(issue_numbers), issue_number)
            return [{"number": number} for number in issue_numbers]

    issues = fetch_issues_from_github(
        FakeGitHubClient(), "owner", "repo", issue_numbers, all_issues=False
    )

    captured = capsys.readouterr()

    assert len(issues) == 52
    assert "🔍 Fetching 52 specific issues..." in captured.out
    assert "⏳ Fetched 1/52 requested issues" in captured.out
    assert "⏳ Fetched 25/52 requested issues" in captured.out
    assert "⏳ Fetched 50/52 requested issues" in captured.out
    assert "⏳ Fetched 52/52 requested issues" in captured.out
    assert "📋 Found 52 issues" in captured.out
