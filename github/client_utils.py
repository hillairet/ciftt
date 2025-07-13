def extract_project_fields(issue_gql_data: dict, field_names: list) -> dict:
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
