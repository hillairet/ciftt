from typing import Optional

import pytest

from ciftt.github.client import FIND_PROJECT_ITEM_BY_QUERY_QUERY, GitHubClient
from ciftt.github.data import IssueNodeInfo, ProjectInfo


def test_update_issue_project_fields_falls_back_to_project_scan(monkeypatch):
    client = GitHubClient(api_key="x")

    def fake_get_project_item_info(owner: str, repo: str, issue_number: int) -> dict:
        return {"projectItems": {"nodes": []}}

    def fake_get_issue_node_id(
        owner: str, repo: str, issue_number: int
    ) -> IssueNodeInfo:
        return IssueNodeInfo(
            id="ISSUE_ID",
            number=issue_number,
            title="T",
            url=f"https://github.com/{owner}/{repo}/issues/{issue_number}",
        )

    def fake_validate_project_exists(owner: str, project_number: str) -> ProjectInfo:
        return ProjectInfo(
            id="PVT_ID",
            title="P",
            number=int(project_number),
            url="https://github.com/orgs/x/projects/1",
            owner=owner,
            type="organization",
        )

    def fake_get_project_field_definitions(owner: str, project_number: str) -> dict:
        return {
            "Priority": {
                "id": "FIELD_ID",
                "dataType": "TEXT",
                "options": [],
            }
        }

    calls = {"update": []}

    def fake_update_project_field(project_id: str, item_id: str, field_id: str, value):
        calls["update"].append((project_id, item_id, field_id, value.model_dump()))
        return {}

    def fake_execute_graphql(query: str, variables: Optional[dict] = None) -> dict:
        if query == FIND_PROJECT_ITEM_BY_QUERY_QUERY:
            assert (variables or {}).get("q") == "10537"
            return {
                "data": {
                    "organization": {
                        "projectV2": {
                            "items": {
                                "nodes": [
                                    {
                                        "id": "PVTI_1",
                                        "content": {
                                            "url": "https://github.com/a/b/issues/1"
                                        },
                                    },
                                    {
                                        "id": "PVTI_MATCH",
                                        "content": {
                                            "url": "https://github.com/cloud-custodian/cloud-custodian/issues/10537"
                                        },
                                    },
                                ],
                            }
                        }
                    }
                }
            }
        return {"data": {}}

    monkeypatch.setattr(client, "get_project_item_info", fake_get_project_item_info)
    monkeypatch.setattr(client, "get_issue_node_id", fake_get_issue_node_id)
    monkeypatch.setattr(client, "validate_project_exists", fake_validate_project_exists)
    monkeypatch.setattr(
        client, "get_project_field_definitions", fake_get_project_field_definitions
    )
    monkeypatch.setattr(client, "update_project_field", fake_update_project_field)
    monkeypatch.setattr(client, "execute_graphql", fake_execute_graphql)

    result = client.update_issue_project_fields(
        owner="cloud-custodian",
        repo="cloud-custodian",
        issue_number=10537,
        project_fields={"Priority": "High"},
        project_owner="stacklet",
        project_number="16",
    )

    assert result.updated_fields == {"Priority": "High"}
    assert result.errors == {}
    assert calls["update"]
    project_id, item_id, field_id, dumped = calls["update"][0]
    assert project_id == "PVT_ID"
    assert item_id == "PVTI_MATCH"
    assert field_id == "FIELD_ID"
    assert dumped == {"text": "High"}


def test_find_org_project_item_id_by_issue_number_uses_query(monkeypatch):
    client = GitHubClient(api_key="x")

    def fake_execute_graphql(query: str, variables: Optional[dict] = None) -> dict:
        assert query == FIND_PROJECT_ITEM_BY_QUERY_QUERY
        assert (variables or {}).get("q") == "25"
        return {
            "data": {
                "organization": {
                    "projectV2": {
                        "items": {
                            "nodes": [
                                {
                                    "id": "PVTI_MATCH",
                                    "content": {"url": "https://x/y/issues/25"},
                                }
                            ]
                        }
                    }
                }
            }
        }

    monkeypatch.setattr(client, "execute_graphql", fake_execute_graphql)

    item_id = client._find_org_project_item_id_by_issue_number(
        org="stacklet",
        project_number="16",
        issue_number=25,
        issue_url="https://x/y/issues/25",
    )

    assert item_id == "PVTI_MATCH"
