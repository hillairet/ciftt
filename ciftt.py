#!/usr/bin/env python3
"""
C.I.F.T.T. - CSV Input for Feature Triage and Tracking
A tool to create or update GitHub issues from CSV input.
"""
from typing import Optional

import typer

from csv_data import CSVData

app = typer.Typer(help="CIFTT - CSV Input for Feature Triage and Tracking")


@app.command()
def main(
    csv_file: str = typer.Argument(
        ..., help="Path to the CSV file containing issue data"
    ),
    repo: str = typer.Argument(..., help="GitHub repository in format 'owner/repo'"),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-d", help="Print actions without executing them"
    ),
):
    """
    Create or update GitHub issues from a CSV file.
    """
    typer.echo(f"🔍 Reading CSV file: {csv_file}")

    try:
        # Load and validate the CSV data
        csv_data = CSVData(csv_file)
        typer.echo(f"✅ Successfully loaded CSV with {len(csv_data.data)} rows")
    except Exception as e:
        typer.echo(f"❌ Error: {e}")
        raise typer.Exit(code=1)

    typer.echo(f"🎯 Target repository: {repo}")

    if dry_run:
        typer.echo("🧪 DRY RUN MODE: No changes will be made on GitHub")

    typer.echo("📋 This is a placeholder. The actual implementation will:")
    typer.echo("  - Connect to GitHub API")
    typer.echo("  - Create or update issues based on CSV data")
    typer.echo("  - Optionally update project fields")


if __name__ == "__main__":
    app()
