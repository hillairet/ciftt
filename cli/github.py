import typer

from github import GitHubClient
from settings import Settings
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


def init_github_client() -> GitHubClient:
    """
    Initialize GitHub client with API token.
    
    Returns:
        GitHubClient instance
        
    Raises:
        typer.Exit: If GitHub client initialization fails
    """
    settings = Settings()
    try:
        github_client = GitHubClient(api_key=settings.github_token.get_secret_value())
        typer.echo("🐙 Connected to GitHub API")
        return github_client
    except Exception as e:
        typer.echo(f"❌ Failed to initialize GitHub client: {e}")
        raise typer.Exit(code=1)
