import typer

from csv_data import CSVData


def load_and_validate_csv(csv_file: str) -> CSVData:
    """
    Load and validate CSV data from a file.
    
    Args:
        csv_file: Path to the CSV file
        
    Returns:
        CSVData instance with loaded data
        
    Raises:
        typer.Exit: If CSV loading fails
    """
    try:
        csv_data = CSVData(csv_file)
        typer.echo(f"💾 Successfully loaded CSV with {len(csv_data.data)} rows")
        return csv_data
    except ValueError as e:
        typer.echo(f"❌ Error: {e}")
        raise typer.Exit(code=1)
