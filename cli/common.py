"""
Common CLI utilities to eliminate code duplication across commands.
"""
from typing import Dict, List, Tuple

import typer

from cli.csv_data import load_and_validate_csv
from cli.github import init_github_client, validate_repository_access, validate_token_scopes
from csv_data import CSVData
from github.client import GitHubClient


def load_csv_for_command(csv_file: str) -> CSVData:
    """
    Common CSV loading logic for all CLI commands.
    
    Args:
        csv_file: Path to the CSV file
        
    Returns:
        CSVData object with loaded and validated data
    """
    typer.echo(f"🔍 Reading CSV file: {csv_file}")
    csv_data = load_and_validate_csv(csv_file)
    typer.echo(f"💾 Successfully loaded CSV with {len(csv_data.data)} rows")
    return csv_data


def setup_github_client_for_command(
    required_scopes: List[str],
    repositories: List[Tuple[str, str]] = None
) -> GitHubClient:
    """
    Initialize and validate GitHub client for CLI commands.
    
    Args:
        required_scopes: List of required OAuth scopes
        repositories: Optional list of (owner, repo) tuples to validate access
        
    Returns:
        Initialized and validated GitHubClient
    """
    github_client = init_github_client()
    
    validate_token_scopes(github_client, required_scopes)
    
    if repositories:
        for owner, repo_name in repositories:
            validate_repository_access(github_client, owner, repo_name)
    
    return github_client


def handle_cli_error(operation_name: str, exception: Exception) -> None:
    """
    Standard error handling for CLI operations.
    
    Args:
        operation_name: Name of the operation that failed
        exception: The exception that was raised
        
    Raises:
        typer.Exit: Always exits with code 1
    """
    typer.echo(f"❌ {operation_name} failed: {exception}")
    raise typer.Exit(code=1)


def validate_project_fields_for_csv(
    csv_data: CSVData,
    github_client: GitHubClient,
    project_owner: str,
    project_number: str
) -> None:
    """
    Validate that CSV project fields exist in the GitHub project.
    
    Args:
        csv_data: CSV data containing project fields
        github_client: GitHub client for API calls
        project_owner: Project owner (user or organization)
        project_number: Project number
        
    Raises:
        typer.Exit: If validation fails
    """
    if not csv_data.has_project_fields():
        return
        
    try:
        field_definitions = github_client.get_project_field_definitions(
            project_owner, project_number
        )

        # Check if all CSV project fields exist in the project
        invalid_fields = []
        valid_fields = []

        for csv_field in csv_data.project_field_columns:
            if csv_field in field_definitions:
                valid_fields.append(csv_field)
            else:
                invalid_fields.append(csv_field)

        if invalid_fields:
            typer.echo(
                f"❌ Invalid project fields found: {', '.join(invalid_fields)}"
            )
            available_fields = list(field_definitions.keys())
            typer.echo(
                f"📋 Available project fields: {', '.join(available_fields)}"
            )
            raise typer.Exit(code=1)
        else:
            typer.echo(f"✅ Project fields validated: {', '.join(valid_fields)}")

    except ValueError as e:
        handle_cli_error("Project field validation", e)