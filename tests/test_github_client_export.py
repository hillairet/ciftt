from typing import Dict, List, Optional, Tuple

from ciftt.github.client import GitHubClient


def make_issue(number: int) -> dict:
    return {"number": number, "title": f"Issue {number}"}


def make_pull_request(number: int) -> dict:
    return {
        "number": number,
        "title": f"Pull request {number}",
        "pull_request": {
            "url": f"https://api.github.com/repos/owner/repo/pulls/{number}"
        },
    }


def test_get_all_issues_fetches_all_rest_pages(monkeypatch):
    client = GitHubClient(api_key="x")
    calls: List[Tuple[str, Dict]] = []

    def fake_get_request(
        endpoint: str, params: Optional[dict] = None, return_headers: bool = False
    ) -> tuple:
        calls.append((endpoint, dict(params or {})))
        page = (params or {}).get("page")
        if page == 1:
            return [make_issue(number) for number in range(1, 101)], {
                "Link": '<https://api.github.com/repositories/1/issues?page=2>; rel="next"'
            }
        if page == 2:
            return [make_issue(101)], {}
        return [], {}

    monkeypatch.setattr(client, "_get_request", fake_get_request)

    issues = client.get_all_issues("owner", "repo", state="all")

    assert [issue["number"] for issue in issues] == list(range(1, 102))
    assert calls == [
        ("repos/owner/repo/issues", {"state": "all", "per_page": 100, "page": 1}),
        ("repos/owner/repo/issues", {"state": "all", "per_page": 100, "page": 2}),
    ]


def test_get_all_issues_follows_next_link_for_short_pages(monkeypatch):
    client = GitHubClient(api_key="x")
    calls: List[Tuple[str, Dict]] = []

    def fake_get_request(
        endpoint: str, params: Optional[dict] = None, return_headers: bool = False
    ) -> tuple:
        calls.append((endpoint, dict(params or {})))
        page = (params or {}).get("page")
        if page == 1:
            return [make_issue(1)], {
                "Link": '<https://api.github.com/repositories/1/issues?page=2>; rel="next"'
            }
        if page == 2:
            return [make_issue(2)], {}
        return [], {}

    monkeypatch.setattr(client, "_get_request", fake_get_request)

    issues = client.get_all_issues("owner", "repo", state="all")

    assert [issue["number"] for issue in issues] == [1, 2]
    assert calls == [
        ("repos/owner/repo/issues", {"state": "all", "per_page": 100, "page": 1}),
        ("repos/owner/repo/issues", {"state": "all", "per_page": 100, "page": 2}),
    ]


def test_get_all_issues_excludes_pull_requests(monkeypatch):
    client = GitHubClient(api_key="x")

    def fake_get_request(
        endpoint: str, params: Optional[dict] = None, return_headers: bool = False
    ) -> tuple:
        if (params or {}).get("page") == 1:
            return [make_issue(1), make_pull_request(2)], {}
        return [], {}

    monkeypatch.setattr(client, "_get_request", fake_get_request)

    issues = client.get_all_issues("owner", "repo", state="all")

    assert [issue["number"] for issue in issues] == [1]


def test_get_all_issues_reports_progress_after_each_page(monkeypatch):
    client = GitHubClient(api_key="x")
    progress_updates = []

    def fake_get_request(
        endpoint: str, params: Optional[dict] = None, return_headers: bool = False
    ) -> tuple:
        page = (params or {}).get("page")
        if page == 1:
            return [make_issue(1), make_pull_request(2)], {
                "Link": '<https://api.github.com/repositories/1/issues?page=2>; rel="next"'
            }
        if page == 2:
            return [make_issue(3)], {}
        return [], {}

    def record_progress(page: int, total_issues: int, page_issues: int) -> None:
        progress_updates.append((page, total_issues, page_issues))

    monkeypatch.setattr(client, "_get_request", fake_get_request)

    client.get_all_issues(
        "owner", "repo", state="all", progress_callback=record_progress
    )

    assert progress_updates == [(1, 1, 1), (2, 2, 1)]


def test_get_issues_by_numbers_excludes_pull_requests(monkeypatch):
    client = GitHubClient(api_key="x")

    def fake_get_request(endpoint: str, params: Optional[dict] = None) -> dict:
        if endpoint == "repos/owner/repo/issues/1":
            return make_issue(1)
        if endpoint == "repos/owner/repo/issues/2":
            return make_pull_request(2)
        raise AssertionError(f"Unexpected endpoint: {endpoint}")

    monkeypatch.setattr(client, "_get_request", fake_get_request)

    issues = client.get_issues_by_numbers("owner", "repo", [1, 2])

    assert [issue["number"] for issue in issues] == [1]


def test_get_issues_by_numbers_reports_progress(monkeypatch):
    client = GitHubClient(api_key="x")
    progress_updates = []

    def fake_get_request(endpoint: str, params: Optional[dict] = None) -> dict:
        issue_number = int(endpoint.rsplit("/", 1)[1])
        return make_issue(issue_number)

    def record_progress(completed: int, total: int, issue_number: int) -> None:
        progress_updates.append((completed, total, issue_number))

    monkeypatch.setattr(client, "_get_request", fake_get_request)

    client.get_issues_by_numbers(
        "owner", "repo", [1, 2, 3], progress_callback=record_progress
    )

    assert progress_updates == [(1, 3, 1), (2, 3, 2), (3, 3, 3)]


def test_get_project_fields_for_issues_reports_progress(monkeypatch):
    client = GitHubClient(api_key="x")
    progress_updates = []

    def fake_execute_graphql(
        _self: GitHubClient, _query: str, variables: Optional[dict] = None
    ) -> dict:
        return {
            "data": {
                "repository": {
                    "issue": {
                        "projectItems": {
                            "nodes": [
                                {
                                    "fieldValues": {
                                        "nodes": [
                                            {
                                                "field": {"name": "Status"},
                                                "name": "Todo",
                                            }
                                        ]
                                    }
                                }
                            ]
                        }
                    }
                }
            }
        }

    def record_progress(completed: int, total: int, issue_number: int) -> None:
        progress_updates.append((completed, total, issue_number))

    monkeypatch.setattr(GitHubClient, "execute_graphql", fake_execute_graphql)

    client.get_project_fields_for_issues(
        "owner",
        "repo",
        [1, 2, 3],
        ["Status"],
        progress_callback=record_progress,
    )

    assert progress_updates == [(1, 3, 1), (2, 3, 2), (3, 3, 3)]
