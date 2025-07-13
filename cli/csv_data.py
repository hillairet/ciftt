import pandas as pd
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


def save_df_to_csv(df: pd.DataFrame, output_file: str) -> None:
    """
    Save DataFrame to CSV file.
    
    Args:
        df: DataFrame to save
        output_file: Path to save the CSV file
        
    Raises:
        typer.Exit: If CSV saving fails
    """
    try:
        df.to_csv(output_file, index=False)
        typer.echo(f"✅ Successfully exported {len(df)} issues to {output_file}")
    except Exception as e:
        typer.echo(f"❌ Failed to write CSV file: {e}")
        raise typer.Exit(code=1)
