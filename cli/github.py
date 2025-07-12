import typer

from utils import parse_repo


def validate_repo(repo: str) -> tuple[str, str]:
    """
    Validate and parse a repository string.
    
    Args:
        repo: Repository string in format 'owner/repo'
        
    Returns:
        Tuple of (owner, repo_name)
        
    Raises:
        typer.Exit: If repository string is invalid
    """
    try:
        owner, repo_name = parse_repo(repo)
        return owner, repo_name
    except ValueError as e:
        typer.echo(f"❌ Error: {e}")
        raise typer.Exit(code=1)
