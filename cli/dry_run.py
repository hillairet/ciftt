import typer

from csv_data import CSVData
from utils import extract_issue_number


def perform_dry_run(csv_data: CSVData) -> None:
    """
    Perform a dry run preview of what issues would be created or updated.
    
    Args:
        csv_data: The CSV data containing issue information
    """
    typer.echo("🧪 DRY RUN MODE: No changes will be made on GitHub")
    for index, row in csv_data.data.iterrows():
        issue_number = extract_issue_number(row.get("url"))
        if issue_number:
            typer.echo(f"Would update issue #{issue_number}: {row['title']}")
        else:
            typer.echo(f"Would create issue: {row['title']}")
