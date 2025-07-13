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


def validate_repository_access(github_client: GitHubClient, owner: str, repo_name: str) -> None:
    """
    Validate that the token has access to the specified repository.
    
    Args:
        github_client: GitHub client instance
        owner: Repository owner
        repo_name: Repository name
        
    Raises:
        typer.Exit: If repository access validation fails
    """
    try:
        # Try to get repository information
        repo_info = github_client._get_request(f"repos/{owner}/{repo_name}")
        typer.echo(f"✅ Repository access confirmed: {owner}/{repo_name}")
        
        # Check if we have write access (needed for creating/updating issues)
        permissions = repo_info.get('permissions', {})
        if not permissions.get('push', False):
            typer.echo(f"⚠️  Warning: Token may not have write access to {owner}/{repo_name}")
            typer.echo("   This could cause issues when creating or updating GitHub issues.")
        
    except Exception as e:
        if "404" in str(e):
            typer.echo(f"❌ Repository not found or no access: {owner}/{repo_name}")
            typer.echo("   Please check:")
            typer.echo("   - Repository exists and is spelled correctly")
            typer.echo("   - Token has access to the repository")
            typer.echo("   - SSO is enabled for the organization (if applicable)")
        else:
            typer.echo(f"❌ Failed to validate repository access: {e}")
        raise typer.Exit(code=1)


def validate_token_scopes(github_client: GitHubClient, required_scopes: list = None) -> None:
    """
    Validate that the token has the required scopes.
    
    Args:
        github_client: GitHub client instance
        required_scopes: List of required scopes (defaults to ['repo'])
        
    Raises:
        typer.Exit: If token doesn't have required scopes
    """
    if required_scopes is None:
        required_scopes = ['repo', 'project']
    
    try:
        # Get token scopes
        _, headers = github_client._request("GET", "user", return_headers=True)
        scopes_header = headers.get('X-OAuth-Scopes', '')
        
        if scopes_header:
            token_scopes = [scope.strip() for scope in scopes_header.split(',') if scope.strip()]
        else:
            token_scopes = []
        
        # Check if required scopes are present
        missing_scopes = [scope for scope in required_scopes if scope not in token_scopes]
        
        if missing_scopes:
            typer.echo(f"❌ Token missing required scopes: {', '.join(missing_scopes)}")
            typer.echo(f"   Current scopes: {', '.join(token_scopes) if token_scopes else 'None'}")
            typer.echo("   Please update your GitHub token with the required scopes.")
            raise typer.Exit(code=1)
        
        typer.echo(f"✅ Token has required scopes: {', '.join(required_scopes)}")
        
    except Exception as e:
        if "typer.Exit" in str(type(e)):
            raise  # Re-raise typer.Exit exceptions
        typer.echo(f"❌ Failed to validate token scopes: {e}")
        raise typer.Exit(code=1)
