# Installation

CIFTT can be installed or run directly from the GitHub repository with `uv`. Choose the workflow that matches what you are trying to do, a shocking innovation in documentation design.

## Recommended: install CIFTT as a command

Use this if you want to run `ciftt` regularly from your shell.

```bash
uv tool install git+https://github.com/hillairet/ciftt
```

Verify the command is available:

```bash
ciftt --help
```

Check your GitHub token and permissions:

```bash
ciftt check-token
```

### Upgrade

To upgrade an existing tool installation:

```bash
uv tool upgrade ciftt
```

If you need to force reinstall from the GitHub repository:

```bash
uv tool install --force git+https://github.com/hillairet/ciftt
```

### Uninstall

```bash
uv tool uninstall ciftt
```

## Run once without installing

Use `uvx` if you want to try CIFTT or run it occasionally without keeping a persistent command installed.

```bash
uvx --from git+https://github.com/hillairet/ciftt ciftt --help
```

Examples:

```bash
uvx --from git+https://github.com/hillairet/ciftt ciftt check-token
uvx --from git+https://github.com/hillairet/ciftt ciftt create-issues input.csv myorg/myrepo
```

You can also run a specific branch, tag, or commit:

```bash
uvx --from git+https://github.com/hillairet/ciftt@main ciftt --help
uvx --from git+https://github.com/hillairet/ciftt@v0.1.0 ciftt --help
```

## Clone for development

Use this workflow if you want to change CIFTT, run tests, or contribute to the project.

```bash
git clone https://github.com/hillairet/ciftt.git
cd ciftt
uv sync
```

Run CIFTT from the development checkout:

```bash
uv run ciftt --help
uv run ciftt check-token
```

Run tests and checks:

```bash
uv run pytest
uv run ruff check .
uv run mypy src
```

## GitHub token configuration

CIFTT needs a GitHub Personal Access Token for GitHub API operations.

Create a token at <https://github.com/settings/tokens/new> with these scopes:

- `repo`: required for creating, updating, and exporting issues
- `project`: required for GitHub Projects v2 operations, including `--project` and `--fields`

Set the token in your shell:

```bash
export GITHUB_TOKEN=your_token_here
```

If your organization uses SSO, authorize the token for that organization after creating it.

The token setup is the same whether you use `uv tool install`, `uvx`, or a cloned development checkout.
