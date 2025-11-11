from ciftt.github.data import (
    DateFieldValue,
    IterationFieldValue,
    NumberFieldValue,
    ProjectFieldValue,
    SingleSelectFieldValue,
    TextFieldValue,
)


def _extract_project_fields(issue_gql_data: dict, field_names: list) -> dict:
    """Extract project fields from an issue's project items."""
    fields = {}

    project_items = issue_gql_data.get("projectItems", {}).get("nodes", [])
    for project_item in project_items:
        field_values = project_item.get("fieldValues", {}).get("nodes", [])
        for field_value in field_values:
            if (
                not field_value
                or "field" not in field_value
                or "name" not in field_value["field"]
            ):
                continue

            field_name = field_value["field"]["name"]

            # Only include requested fields
            if field_name not in field_names:
                continue

            # Extract the value based on the field type
            if "text" in field_value:
                fields[field_name] = field_value["text"]
            elif "number" in field_value:
                fields[field_name] = field_value["number"]
            elif "date" in field_value:
                fields[field_name] = field_value["date"]
            elif "name" in field_value:
                fields[field_name] = field_value["name"]

    return fields


def _format_project_field_value(
    field_type: str,
    value: str,
    field_options: list = None,
    field_iterations: list = None,
) -> ProjectFieldValue:
    """
    Format a field value for GitHub GraphQL API based on field type.

    Args:
        field_type: The field data type from GitHub (TEXT, NUMBER, DATE, SINGLE_SELECT, etc.)
        value: The value to format
        field_options: List of valid options for single select fields

    Returns:
        Dictionary formatted for GitHub GraphQL API
    """
    if not value or str(value).strip() == "":
        return None

    value_str = str(value).strip()

    if field_type == "TEXT":
        return TextFieldValue(text=value_str)
    elif field_type == "NUMBER":
        try:
            return NumberFieldValue(number=float(value_str))
        except ValueError as e:
            raise ValueError(f"Invalid number value: {value_str}") from e
    elif field_type == "DATE":
        # Expecting ISO date format (YYYY-MM-DD)
        return DateFieldValue(date=value_str)
    elif field_type == "SINGLE_SELECT":
        if not field_options:
            raise ValueError("Single select field options are required")

        # Find the option ID by name
        option_id = None
        for option in field_options:
            if option.get("name") == value_str:
                option_id = option.get("id")
                break

        if not option_id:
            valid_options = [opt.get("name") for opt in field_options]
            raise ValueError(
                f"Invalid option '{value_str}'. Valid options: {valid_options}"
            )

        return SingleSelectFieldValue(singleSelectOptionId=option_id)
    elif field_type == "ITERATION":
        if not field_iterations:
            raise ValueError("Iteration field iterations are required")

        # Find the iteration ID by title
        iteration_id = None
        for iteration in field_iterations:
            if iteration.get("title") == value_str:
                iteration_id = iteration.get("id")
                break

        if not iteration_id:
            valid_iterations = [iter.get("title") for iter in field_iterations]
            raise ValueError(
                f"Invalid iteration '{value_str}'. Valid iterations: {valid_iterations}"
            )

        return IterationFieldValue(iterationId=iteration_id)
    else:
        raise ValueError(f"Unsupported field type: {field_type}")


def _extract_project_info_for_updates(issue_data: dict) -> dict:
    """
    Extract project information needed for updating fields.

    Args:
        issue_data: Issue data from get_project_item_info GraphQL query

    Returns:
        Dictionary mapping project titles to their info (project_id, item_id, fields)
    """
    projects = {}

    project_items = issue_data.get("projectItems", {}).get("nodes", [])
    for project_item in project_items:
        project = project_item.get("project", {})
        project_title = project.get("title")

        if not project_title:
            continue

        # Create fields lookup by name
        fields_by_name = {}
        project_fields = project.get("fields", {}).get("nodes", [])
        for field in project_fields:
            field_name = field.get("name")
            if field_name:
                field_def = {
                    "id": field.get("id"),
                    "dataType": field.get("dataType"),
                    "options": field.get("options", []),
                }

                # Handle iteration fields
                if field.get("configuration") and field["configuration"].get(
                    "iterations"
                ):
                    field_def["iterations"] = field["configuration"]["iterations"]

                fields_by_name[field_name] = field_def

        projects[project_title] = {
            "project_id": project.get("id"),
            "project_number": project.get("number"),
            "item_id": project_item.get("id"),
            "fields": fields_by_name,
        }

    return projects
