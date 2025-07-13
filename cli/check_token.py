import typer

from cli.github import init_github_client


def check_token() -> None:
    """Check GitHub token validity and permissions."""
    typer.echo("🔍 Checking GitHub token...")
    
    try:
        github_client = init_github_client()
        
        # Get user info and headers to validate token and check scopes
        user_info, headers = github_client._request("GET", "user", return_headers=True)
        typer.echo(f"✅ Token is valid for user: {user_info['login']}")
        
        # Check token scopes from headers
        scopes_header = headers.get('X-OAuth-Scopes', '')
        if scopes_header:
            scopes = [scope.strip() for scope in scopes_header.split(',') if scope.strip()]
            typer.echo(f"🔑 Token scopes: {', '.join(scopes)}")
        else:
            typer.echo("🔑 Token scopes: None or unable to determine")
        
        # Check organizations
        try:
            orgs = github_client._get_request("user/orgs")
            if orgs:
                org_names = [org['login'] for org in orgs]
                typer.echo(f"🏢 Authorized organizations: {', '.join(org_names)}")
            else:
                typer.echo("🏢 Authorized organizations: None")
        except Exception as e:
            typer.echo(f"🏢 Could not fetch organizations: {e}")
        
        # Check rate limits
        rate_limit = github_client._get_request("rate_limit")
        core_limit = rate_limit['resources']['core']
        typer.echo(f"📊 Rate limit: {core_limit['remaining']}/{core_limit['limit']} remaining")
        
    except Exception as e:
        typer.echo(f"❌ Token validation failed: {e}")
        raise typer.Exit(code=1)
