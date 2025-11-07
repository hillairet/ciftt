# AGENTS.md

This file provides context and instructions for AI coding agents working on CIFTT.

## Project Overview

CIFTT (CSV Input for Feature Triage and Tracking) is a Python CLI tool that automates creating and updating GitHub issues from CSV/TSV files. It integrates with both GitHub's REST API (for basic issue operations) and GraphQL API (for GitHub Projects v2 field updates).

### Key Features
- Create GitHub issues in bulk from CSV/TSV files
- Update existing issues and their GitHub Project v2 fields
- Export issues with project field values to CSV
- Token validation and permission checking
- Dry-run mode for safe testing

### Technology Stack
- **Python 3.8+** with modern tooling (uv, ruff, mypy, pytest)
- **CLI Framework**: Typer (not argparse or click)
- **Data Validation**: Pydantic v2 for models and settings
- **Data Processing**: Pandas for CSV/TSV handling
- **HTTP Client**: Requests for GitHub API calls
- **Testing**: Pytest with fixtures and integration tests

### Project Structure
```
ciftt/
├── src/ciftt/           # Source code (src-layout structure)
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli/             # CLI command implementations
│   ├── github/          # GitHub API client and utilities
│   ├── settings.py      # Pydantic Settings configuration
│   ├── csv_data.py      # CSV/TSV parsing and data models
│   ├── transform.py     # Data transformation utilities
│   └── utils.py         # General utilities
├── tests/               # Test suite
│   ├── integration/     # Integration tests
│   └── fixtures/        # Test fixtures and sample data
├── Taskfile.yml         # Task runner configuration (task commands)
├── pyproject.toml       # Project configuration and dependencies
└── README.md            # User-facing documentation
```

## Development Setup

### Prerequisites
- Python 3.8 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- [Task](https://taskfile.dev/) task runner (optional but recommended)
- GitHub personal access token with `repo` and `project` scopes

### Installation

```bash
# Install dependencies using uv (recommended)
uv sync

# OR manually create a virtual environment
python -m venv ENV
source ENV/bin/activate  # or ENV/bin/activate.fish for fish shell
pip install -e ".[dev]"
```

### Environment Setup

Create a `.env` file in the project root:
```bash
GITHUB_TOKEN=your_github_personal_access_token
```

Or export the token directly:
```bash
export GITHUB_TOKEN=your_github_personal_access_token
```

**Token Requirements**:
- `repo` scope: Required for all operations (creating, updating, exporting issues)
- `project` scope: Required when using `--project` option or `--fields` option
- For organizations with SSO, token must be authorized for that organization

## Build and Test Commands

The project uses [Task](https://taskfile.dev/) for common development workflows. All tasks are defined in `Taskfile.yml`.

### Running Tests

```bash
# Run tests with coverage (requires 80% minimum)
task test
# OR directly with uv
uv run pytest
```

### Code Quality

```bash
# Run all quality checks (test, lint, format-check, typecheck)
task check

# Run individual checks
task lint           # Run ruff linter
task format-check   # Check code formatting
task typecheck      # Run mypy type checking

# Auto-fix issues
task fix            # Auto-fix linting and formatting
task format         # Format code with ruff
```

### Cleaning Up

```bash
task clean  # Remove generated files (.venv, .coverage, caches, etc.)
```

## Code Style Guidelines

### Formatting and Linting
- **Formatter**: Ruff (replaces Black, line length 88)
- **Linter**: Ruff (replaces Flake8, isort)
- **Type Checker**: Mypy (relaxed strictness for gradual adoption)

### Code Conventions
- **NO COMMENTS** unless absolutely necessary for complex logic
- **Return Early Pattern**: Avoid deep nesting by returning/continuing early
- **Extract Functions**: When indentation gets deep (3+ levels), extract to a new function
- **All imports at top**: No inline imports
- **Case Sensitivity**: CSV column names are case-sensitive (Title, Description, URL, etc.)

### Example: Early Return Pattern
```python
# Good - Early return reduces nesting
def process_issue(issue_data):
    if not issue_data.get('title'):
        return None

    if not validate_issue(issue_data):
        return None

    return create_issue(issue_data)

# Avoid - Deep nesting
def process_issue(issue_data):
    if issue_data.get('title'):
        if validate_issue(issue_data):
            return create_issue(issue_data)
    return None
```

## Testing Guidelines

### Test Organization
- Unit tests in `tests/` directory
- Integration tests in `tests/integration/`
- Fixtures in `tests/integration/fixtures/`
- Sample CSV files in project root: `sample_create.csv`, `sample_update.tsv`

### Testing Principles
- **NO one-off command-line tests**: Create reusable unit/integration tests instead
- All test code should be committed to the repository
- Prefer automated tests that can run repeatedly in CI/CD
- Test both success and error cases
- Use pytest fixtures for test data

### Running Specific Tests
```bash
pytest tests/integration/           # Integration tests only
pytest -k test_create_issues        # Run specific test
pytest --cov=src/ciftt              # Coverage report
```

## Git Conventions

**IMPORTANT**: DO NOT use conventional commits.

### Commit Message Format
Use **gitmojis** for commit messages:
- ✨ `:sparkles:` for features
- ♻️ `:recycle:` for refactoring
- 🐛 `:bug:` for bug fixes
- ✅ `:white_check_mark:` for tests
- 📝 `:memo:` for documentation
- 🎨 `:art:` for style/formatting

Examples:
```
✨ add support for TSV file format
♻️ refactor CSV parsing to use pandas
🐛 fix rate limit handling in GitHub client
✅ add tests for project field validation
```

## CLI Usage Examples

```bash
# Validate GitHub token
python -m ciftt check-token

# Create issues from CSV
python -m ciftt create-issues input.csv owner/repo

# Update issues (basic fields only)
python -m ciftt update-issues input.csv

# Update issues AND project fields
python -m ciftt update-issues input.csv --project owner/123

# Export issues to CSV
python -m ciftt export-issues owner/repo output.csv

# Export with project fields
python -m ciftt export-issues owner/repo output.csv --fields "Priority,Status,Sprint"

# Dry-run mode (no actual changes)
python -m ciftt update-issues input.csv --project owner/123 --dry-run
```

## Important Implementation Details

### CSV/TSV Handling
- Supports both CSV (comma-separated) and TSV (tab-separated) files
- Auto-detects format based on file extension (`.csv` or `.tsv`)
- Column names are **case-sensitive**: Use `Title`, `Description`, `Labels`, `Assignee`, `URL`
- Required columns:
  - `Title` required for creating issues
  - `URL` required for updating issues
- Labels are **completely replaced**, not merged (include all labels you want to keep in CSV)

### GitHub Project v2 Fields
- Any column not recognized as standard issue field is treated as a Project field
- Supported field types: TEXT, NUMBER, SINGLE_SELECT, ITERATION (Sprint fields)
- Project field updates only work with `update-issues` (not `create-issues`)
- `--project` option required to update project fields
- Validates project exists and fields are valid before processing

### API Usage
- REST API for basic issue operations (create, update, export)
- GraphQL API for GitHub Projects v2 field operations
- Automatic rate limit handling with retries
- Token scope validation before operations

### Error Handling
- Early validation of tokens, repositories, and projects
- Clear error messages for permission issues and missing scopes
- SSO authorization detection for organization access
- Dry-run mode for safe testing before making changes

## Security Considerations

- Never commit `.env` files or tokens to version control
- GitHub token requires minimum scopes (`repo` and optionally `project`)
- Validate all user inputs from CSV files
- Be aware of GitHub API rate limits (token validation command shows current limits)

## Common Development Tasks

### Adding a New CLI Command
1. Create new module in `src/ciftt/cli/`
2. Import and register in `src/ciftt/__init__.py`
3. Add tests in `tests/`
4. Update README.md with usage examples

### Adding GitHub API Support
1. Add methods to `src/ciftt/github/client.py`
2. Use existing rate limit handling and error handling patterns
3. Add GraphQL queries to `src/ciftt/github/queries/` if needed
4. Update data models in `src/ciftt/github/data.py`

### Updating CSV Schema
1. Update column mappings in `src/ciftt/csv_data.py`
2. Update validation logic
3. Update sample CSV files in project root
4. Update README.md documentation

## Package Management

The project uses **uv** for modern Python package management:

```bash
# Install/sync dependencies
uv sync

# Add a new dependency
uv add package-name

# Add a dev dependency
uv add --dev package-name

# Run commands in the uv environment
uv run pytest
uv run python -m ciftt check-token
```

## Current Development Status

Check the Roadmap section in README.md for current feature status. Recent work includes:
- ✅ GitHub Project v2 field updates
- ✅ Flexible project identifier formats
- 📝 CSV validation improvements (in progress)

## Deployment

CIFTT is a CLI tool, not a deployed service:
- Users clone the repository or install via pip (future)
- Run directly with `python -m ciftt` or `task` commands
- No server deployment or hosting required

## Additional Resources

- **README.md**: User-facing documentation and feature overview
- **CLAUDE.md**: Project-specific guidance for Claude Code AI assistant
- **CONVENTIONS.md**: Development conventions (legacy, mostly superseded by this file)
- **Taskfile.yml**: All available task commands and their implementations
- **pyproject.toml**: Complete project configuration, dependencies, and tool settings
