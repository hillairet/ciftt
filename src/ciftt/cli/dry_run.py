import typer

from ciftt.csv_data import CSVData
from ciftt.utils import extract_issue_number


def perform_dry_run(csv_data: CSVData) -> None:
    """
    Perform a dry run preview of what issues would be created or updated.

    Args:
        csv_data: The CSV data containing issue information
    """
    typer.echo("🧪 DRY RUN MODE: No changes will be made on GitHub")
    for index, row in csv_data.data.iterrows():
        issue_number = extract_issue_number(row.get("URL"))
        if issue_number:
            title = row.get("Title", "(no title change)")
            typer.echo(f"Would update issue #{issue_number}: {title}")

            # Show project fields that would be updated
            project_fields = csv_data.get_project_field_data(index)
            if project_fields:
                field_updates = [
                    f"{name}='{value}'" for name, value in project_fields.items()
                ]
                typer.echo(
                    f"  📊 Would update project fields: {', '.join(field_updates)}"
                )
        else:
            title = row.get("Title", "(no title)")
            typer.echo(f"Would create issue: {title}")
