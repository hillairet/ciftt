from ciftt.github.client import GitHubClient


def test_get_repository_node_id_returns_id(monkeypatch):
    client = GitHubClient(api_key="token")
    calls = []

    def fake_execute_graphql(self, query, variables=None):
        calls.append((query, variables))
        return {"data": {"repository": {"id": "R_target"}}}

    monkeypatch.setattr(GitHubClient, "execute_graphql", fake_execute_graphql)

    assert client.get_repository_node_id("target-org", "target-repo") == "R_target"
    assert calls[0][1] == {"owner": "target-org", "repo": "target-repo"}


def test_get_transfer_issue_info_returns_parent_number(monkeypatch):
    client = GitHubClient(api_key="token")

    def fake_execute_graphql(self, query, variables=None):
        return {
            "data": {
                "repository": {
                    "issue": {
                        "id": "I_source",
                        "number": 42,
                        "url": "https://github.com/source/repo/issues/42",
                        "state": "CLOSED",
                        "parent": {"number": 12},
                    }
                }
            }
        }

    monkeypatch.setattr(GitHubClient, "execute_graphql", fake_execute_graphql)

    info = client.get_transfer_issue_info("source", "repo", 42)

    assert info.id == "I_source"
    assert info.number == 42
    assert info.state == "CLOSED"
    assert info.parent_number == 12


def test_transfer_issue_returns_destination(monkeypatch):
    client = GitHubClient(api_key="token")

    def fake_execute_graphql(self, query, variables=None):
        assert variables == {"issueId": "I_source", "repositoryId": "R_target"}
        return {
            "data": {
                "transferIssue": {
                    "issue": {
                        "id": "I_dest",
                        "number": 101,
                        "url": "https://github.com/target/repo/issues/101",
                    }
                }
            }
        }

    monkeypatch.setattr(GitHubClient, "execute_graphql", fake_execute_graphql)

    issue = client.transfer_issue("I_source", "R_target")

    assert issue.id == "I_dest"
    assert issue.number == 101
    assert issue.url == "https://github.com/target/repo/issues/101"


def test_mutations_raise_value_error_on_graphql_errors(monkeypatch):
    client = GitHubClient(api_key="token")

    def fake_execute_graphql(self, query, variables=None):
        return {"errors": [{"message": "boom"}]}

    monkeypatch.setattr(GitHubClient, "execute_graphql", fake_execute_graphql)

    try:
        client.close_issue("I_dest")
    except ValueError as exc:
        assert "boom" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
