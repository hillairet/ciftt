import pytest

from ciftt.github.client_utils import (
    _extract_project_fields,
    _extract_project_info_for_updates,
    _format_project_field_value,
)
from ciftt.github.data import (
    DateFieldValue,
    IterationFieldValue,
    NumberFieldValue,
    SingleSelectFieldValue,
    TextFieldValue,
)


class TestExtractProjectFields:
    def test_extract_text_field(self):
        issue_gql_data = {
            "projectItems": {
                "nodes": [
                    {
                        "fieldValues": {
                            "nodes": [
                                {
                                    "field": {"name": "Status"},
                                    "text": "In Progress",
                                }
                            ]
                        }
                    }
                ]
            }
        }
        field_names = ["Status"]

        result = _extract_project_fields(issue_gql_data, field_names)

        assert result == {"Status": "In Progress"}

    def test_extract_number_field(self):
        issue_gql_data = {
            "projectItems": {
                "nodes": [
                    {
                        "fieldValues": {
                            "nodes": [
                                {
                                    "field": {"name": "Priority"},
                                    "number": 3,
                                }
                            ]
                        }
                    }
                ]
            }
        }
        field_names = ["Priority"]

        result = _extract_project_fields(issue_gql_data, field_names)

        assert result == {"Priority": 3}

    def test_extract_date_field(self):
        issue_gql_data = {
            "projectItems": {
                "nodes": [
                    {
                        "fieldValues": {
                            "nodes": [
                                {
                                    "field": {"name": "Due Date"},
                                    "date": "2025-12-31",
                                }
                            ]
                        }
                    }
                ]
            }
        }
        field_names = ["Due Date"]

        result = _extract_project_fields(issue_gql_data, field_names)

        assert result == {"Due Date": "2025-12-31"}

    def test_extract_name_field(self):
        issue_gql_data = {
            "projectItems": {
                "nodes": [
                    {
                        "fieldValues": {
                            "nodes": [
                                {
                                    "field": {"name": "Assignee"},
                                    "name": "John Doe",
                                }
                            ]
                        }
                    }
                ]
            }
        }
        field_names = ["Assignee"]

        result = _extract_project_fields(issue_gql_data, field_names)

        assert result == {"Assignee": "John Doe"}

    def test_extract_multiple_fields(self):
        issue_gql_data = {
            "projectItems": {
                "nodes": [
                    {
                        "fieldValues": {
                            "nodes": [
                                {
                                    "field": {"name": "Status"},
                                    "text": "Done",
                                },
                                {
                                    "field": {"name": "Priority"},
                                    "number": 1,
                                },
                            ]
                        }
                    }
                ]
            }
        }
        field_names = ["Status", "Priority"]

        result = _extract_project_fields(issue_gql_data, field_names)

        assert result == {"Status": "Done", "Priority": 1}

    def test_filter_by_requested_field_names(self):
        issue_gql_data = {
            "projectItems": {
                "nodes": [
                    {
                        "fieldValues": {
                            "nodes": [
                                {
                                    "field": {"name": "Status"},
                                    "text": "Done",
                                },
                                {
                                    "field": {"name": "Priority"},
                                    "number": 1,
                                },
                            ]
                        }
                    }
                ]
            }
        }
        field_names = ["Status"]

        result = _extract_project_fields(issue_gql_data, field_names)

        assert result == {"Status": "Done"}
        assert "Priority" not in result

    def test_skip_field_value_without_field_key(self):
        issue_gql_data = {
            "projectItems": {
                "nodes": [
                    {
                        "fieldValues": {
                            "nodes": [
                                None,
                                {},
                                {"text": "value"},
                                {
                                    "field": {"name": "Status"},
                                    "text": "Done",
                                },
                            ]
                        }
                    }
                ]
            }
        }
        field_names = ["Status"]

        result = _extract_project_fields(issue_gql_data, field_names)

        assert result == {"Status": "Done"}

    def test_empty_project_items(self):
        issue_gql_data = {"projectItems": {"nodes": []}}
        field_names = ["Status"]

        result = _extract_project_fields(issue_gql_data, field_names)

        assert result == {}

    def test_missing_project_items_key(self):
        issue_gql_data = {}
        field_names = ["Status"]

        result = _extract_project_fields(issue_gql_data, field_names)

        assert result == {}


class TestFormatProjectFieldValue:
    def test_format_text_field(self):
        result = _format_project_field_value("TEXT", "Hello World")

        assert isinstance(result, TextFieldValue)
        assert result.text == "Hello World"

    def test_format_text_field_with_whitespace(self):
        result = _format_project_field_value("TEXT", "  Hello  ")

        assert isinstance(result, TextFieldValue)
        assert result.text == "Hello"

    def test_format_number_field(self):
        result = _format_project_field_value("NUMBER", "42")

        assert isinstance(result, NumberFieldValue)
        assert result.number == 42.0

    def test_format_number_field_with_float(self):
        result = _format_project_field_value("NUMBER", "3.14")

        assert isinstance(result, NumberFieldValue)
        assert result.number == 3.14

    def test_format_number_field_invalid_value(self):
        with pytest.raises(ValueError, match="Invalid number value: abc"):
            _format_project_field_value("NUMBER", "abc")

    def test_format_date_field(self):
        result = _format_project_field_value("DATE", "2025-12-31")

        assert isinstance(result, DateFieldValue)
        assert result.date == "2025-12-31"

    def test_format_single_select_field(self):
        field_options = [
            {"id": "opt1", "name": "Low"},
            {"id": "opt2", "name": "High"},
        ]

        result = _format_project_field_value(
            "SINGLE_SELECT", "High", field_options=field_options
        )

        assert isinstance(result, SingleSelectFieldValue)
        assert result.singleSelectOptionId == "opt2"

    def test_format_single_select_field_without_options(self):
        with pytest.raises(
            ValueError, match="Single select field options are required"
        ):
            _format_project_field_value("SINGLE_SELECT", "High")

    def test_format_single_select_field_invalid_option(self):
        field_options = [
            {"id": "opt1", "name": "Low"},
            {"id": "opt2", "name": "High"},
        ]

        with pytest.raises(ValueError, match="Invalid option 'Medium'. Valid options:"):
            _format_project_field_value(
                "SINGLE_SELECT", "Medium", field_options=field_options
            )

    def test_format_iteration_field(self):
        field_iterations = [
            {"id": "iter1", "title": "Sprint 1"},
            {"id": "iter2", "title": "Sprint 2"},
        ]

        result = _format_project_field_value(
            "ITERATION", "Sprint 2", field_iterations=field_iterations
        )

        assert isinstance(result, IterationFieldValue)
        assert result.iterationId == "iter2"

    def test_format_iteration_field_without_iterations(self):
        with pytest.raises(ValueError, match="Iteration field iterations are required"):
            _format_project_field_value("ITERATION", "Sprint 1")

    def test_format_iteration_field_invalid_iteration(self):
        field_iterations = [
            {"id": "iter1", "title": "Sprint 1"},
            {"id": "iter2", "title": "Sprint 2"},
        ]

        with pytest.raises(
            ValueError, match="Invalid iteration 'Sprint 3'. Valid iterations:"
        ):
            _format_project_field_value(
                "ITERATION", "Sprint 3", field_iterations=field_iterations
            )

    def test_format_empty_value_returns_none(self):
        result = _format_project_field_value("TEXT", "")
        assert result is None

    def test_format_whitespace_only_value_returns_none(self):
        result = _format_project_field_value("TEXT", "   ")
        assert result is None

    def test_format_none_value_returns_none(self):
        result = _format_project_field_value("TEXT", None)
        assert result is None

    def test_format_unsupported_field_type(self):
        with pytest.raises(ValueError, match="Unsupported field type: UNKNOWN"):
            _format_project_field_value("UNKNOWN", "value")


class TestExtractProjectInfoForUpdates:
    def test_extract_single_project_with_fields(self):
        issue_data = {
            "projectItems": {
                "nodes": [
                    {
                        "id": "item1",
                        "project": {
                            "id": "proj1",
                            "number": 1,
                            "title": "My Project",
                            "fields": {
                                "nodes": [
                                    {
                                        "id": "field1",
                                        "name": "Status",
                                        "dataType": "SINGLE_SELECT",
                                        "options": [
                                            {"id": "opt1", "name": "Todo"},
                                            {"id": "opt2", "name": "Done"},
                                        ],
                                    },
                                    {
                                        "id": "field2",
                                        "name": "Priority",
                                        "dataType": "NUMBER",
                                        "options": [],
                                    },
                                ]
                            },
                        },
                    }
                ]
            }
        }

        result = _extract_project_info_for_updates(issue_data)

        assert "My Project" in result
        project = result["My Project"]
        assert project["project_id"] == "proj1"
        assert project["project_number"] == 1
        assert project["item_id"] == "item1"
        assert "Status" in project["fields"]
        assert "Priority" in project["fields"]
        assert project["fields"]["Status"]["id"] == "field1"
        assert project["fields"]["Status"]["dataType"] == "SINGLE_SELECT"
        assert len(project["fields"]["Status"]["options"]) == 2

    def test_extract_project_with_iteration_field(self):
        issue_data = {
            "projectItems": {
                "nodes": [
                    {
                        "id": "item1",
                        "project": {
                            "id": "proj1",
                            "number": 1,
                            "title": "Sprint Project",
                            "fields": {
                                "nodes": [
                                    {
                                        "id": "field1",
                                        "name": "Sprint",
                                        "dataType": "ITERATION",
                                        "options": [],
                                        "configuration": {
                                            "iterations": [
                                                {"id": "iter1", "title": "Sprint 1"},
                                                {"id": "iter2", "title": "Sprint 2"},
                                            ]
                                        },
                                    }
                                ]
                            },
                        },
                    }
                ]
            }
        }

        result = _extract_project_info_for_updates(issue_data)

        assert "Sprint Project" in result
        project = result["Sprint Project"]
        assert "Sprint" in project["fields"]
        assert "iterations" in project["fields"]["Sprint"]
        assert len(project["fields"]["Sprint"]["iterations"]) == 2

    def test_extract_multiple_projects(self):
        issue_data = {
            "projectItems": {
                "nodes": [
                    {
                        "id": "item1",
                        "project": {
                            "id": "proj1",
                            "number": 1,
                            "title": "Project 1",
                            "fields": {"nodes": []},
                        },
                    },
                    {
                        "id": "item2",
                        "project": {
                            "id": "proj2",
                            "number": 2,
                            "title": "Project 2",
                            "fields": {"nodes": []},
                        },
                    },
                ]
            }
        }

        result = _extract_project_info_for_updates(issue_data)

        assert len(result) == 2
        assert "Project 1" in result
        assert "Project 2" in result
        assert result["Project 1"]["project_id"] == "proj1"
        assert result["Project 2"]["project_id"] == "proj2"

    def test_skip_project_without_title(self):
        issue_data = {
            "projectItems": {
                "nodes": [
                    {
                        "id": "item1",
                        "project": {
                            "id": "proj1",
                            "number": 1,
                            "fields": {"nodes": []},
                        },
                    }
                ]
            }
        }

        result = _extract_project_info_for_updates(issue_data)

        assert len(result) == 0

    def test_skip_field_without_name(self):
        issue_data = {
            "projectItems": {
                "nodes": [
                    {
                        "id": "item1",
                        "project": {
                            "id": "proj1",
                            "number": 1,
                            "title": "My Project",
                            "fields": {
                                "nodes": [
                                    {
                                        "id": "field1",
                                        "dataType": "TEXT",
                                        "options": [],
                                    }
                                ]
                            },
                        },
                    }
                ]
            }
        }

        result = _extract_project_info_for_updates(issue_data)

        assert "My Project" in result
        assert len(result["My Project"]["fields"]) == 0

    def test_empty_project_items(self):
        issue_data = {"projectItems": {"nodes": []}}

        result = _extract_project_info_for_updates(issue_data)

        assert result == {}

    def test_missing_project_items_key(self):
        issue_data = {}

        result = _extract_project_info_for_updates(issue_data)

        assert result == {}
