# CLAUDE.md

This file provides project-specific guidance for Claude Code when working on CIFTT.

## Project Overview

CIFTT (CSV Input for Feature Triage and Tracking) is a Python CLI tool that automates the process of creating and updating GitHub issues from CSV files. It uses GitHub's REST and GraphQL APIs to interact with repositories and GitHub Projects v2.

## Architecture

- **Main CLI**: `ciftt.py` - Entry point using Typer CLI framework
- **CLI Commands**: `cli/` directory contains individual command implementations
- **GitHub Integration**: `github/` directory handles API interactions
- **Data Processing**: `csv_data.py` and `transform.py` handle CSV parsing and data transformation
- **Configuration**: `settings.py` uses Pydantic Settings for environment-based config

## Key Technologies

- **CLI Framework**: Typer (not argparse or click)
- **Data Validation**: Pydantic v2 for models and settings
- **Data Processing**: Pandas for CSV handling
- **HTTP Client**: Requests for API calls
- **Testing**: Pytest with fixtures and integration tests

## Development Standards

### Code Style
- **Formatters**: Black (line length 88), isort
- **Linter**: Flake8
- **No comments** unless absolutely necessary for complex logic
- Use Return Early pattern to avoid deep nesting
- Extract functions when indentation gets too deep
- All imports at top of files

### Git Conventions
- **DO NOT** use conventional commits
- **USE** gitmojis instead:
  - ✨ `:sparkles:` for features  
  - ♻️ `:recycle:` for refactoring
  - 🐛 `:bug:` for bug fixes

### Testing
- Tests in `tests/` directory
- Integration tests in `tests/integration/`
- Use pytest fixtures for test data
- Test both success and error cases
- Run tests with: `pytest`

## Common Commands

```bash
# Development setup
python -m venv ENV
source ENV/bin/activate  # or ENV/bin/activate.fish
pip install -e ".[dev]"  # installs project in development mode

# Code quality checks
black --exclude="ENV" .
isort --skip=ENV .
flake8 --exclude=ENV

# Testing
pytest                      # runs all tests
pytest tests/integration/  # integration tests only
pytest -k test_name        # run specific test

# CLI usage examples
python ciftt.py check-token
python ciftt.py create-issues input.csv owner/repo
python ciftt.py update-issues input.csv owner/123  # project format
python ciftt.py export-issues owner/repo output.csv
```

## Environment Setup

- Requires `GITHUB_TOKEN` environment variable
- Can use `.env` file for local development
- Token needs `repo` and `project` scopes
- For organizations with SSO, token must be authorized

## Current Branch Context

Working on `feature/github-project-fields` branch which adds:
- GitHub Project v2 field updates (`cli/update_issues.py`)
- Project field detection in CSV data (`csv_data.py`)
- GraphQL integration for Projects v2 (`github/client.py`)
- Support for iteration fields like Sprint

## File Structure Notes

- Sample CSV files in root: `sample_create.csv`, `sample_update.tsv`, `sample_create_update.tsv`
- GraphQL queries in `github/queries/`
- Integration test fixtures in `tests/integration/fixtures/`
- Virtual environment in `ENV/` (excluded from git)

## Important Implementation Details

- **Case Sensitivity**: CSV columns are case-sensitive (Title, Description, URL, etc. must use proper case)
- **Required Columns**: Only `Title` column is required for issue creation; `URL` column required for updates
- **Project Fields**: Any column not recognized as a standard issue field is treated as a GitHub Project v2 field
- **Supported Project Field Types**: TEXT, NUMBER, SINGLE_SELECT, ITERATION (Sprint fields)
- **Project Validation**: Validates project exists and fields are valid before processing issues
- **Dry-run Mode**: Supports `--dry-run` flag for testing without making changes
- **Rate Limiting**: GitHub API rate limiting handled automatically with retries
- **Token Validation**: Validates GitHub token permissions (`repo` and `project` scopes) before operations
- **API Usage**: Uses GitHub GraphQL API for Projects v2 fields, REST API for basic issue operations