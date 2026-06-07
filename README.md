<p align="center">
  <img src="assets/ciftty.webp" alt="CIFTT Logo" width="300"/>
</p>

# CIFTT
> *CSV Input for Feature Triage and Tracking*

**CIFTT** turns your soul-crushing spreadsheets into structured GitHub issues and project entries—because if you’re going to suffer, at least automate it.

---

## 🧠 Why use CIFTT?

It’s Friday afternoon.

You’re *almost* free. Your brain is halfway out the door, already thinking about nachos or silence or both.

Then it happens.
A spreadsheet lands in your inbox with **200 feature requests**. Two. Hundred.

Your manager wants them in GitHub. Tracked. Tagged. Assigned.
Beautifully sorted into your GitHub Project like some kind of agile wizard.

But GitHub doesn’t let you bulk upload to Projects.
You have three options:

1. Spend the rest of your day (and soul) copying and pasting until your mouse becomes an extension of your sadness.
2. Resign yourself to “just using the spreadsheet” and pretending that's fine (it’s not).
3. Or—you know—**use CIFTT**, feed it that cursed CSV, and go live your life.

CIFTT automates the pain away.
It parses your spreadsheet and creates GitHub issues, fills in Projects fields, and gives you back your weekend.

You deserve better. Let the robot do the boring part.

---

## 🗺️ Roadmap

| Feature                                                                | Status         |
|------------------------------------------------------------------------|----------------|
| Create issues in a GitHub repository with basic fields                 | ✅ Done        |
| Update basic fields of existing issues in a GitHub repository          | ✅ Done        |
| Set GitHub Project v2 fields when updating issues                      | ✅ Done        |
| Support flexible project identifier formats                            | ✅ Done        |
| Validate GitHub Project field values in the CSV                        | 📝 To Do       |
| Validate labels and assignees in the CSV before creating/updating      | 📝 To Do       |
| Provide tips and examples to help prepare the CSV                      | 📝 To Do       |

---

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- [uv](https://github.com/astral-sh/uv) package manager

### Setup

1. **Install CIFTT**

Use `uv tool install` to install CIFTT directly from the GitHub repository:

```bash
uv tool install git+https://github.com/hillairet/ciftt
```

Verify the command is available:

```bash
ciftt --help
```

For one-off runs with `uvx` or development setup with `uv sync`, see the [installation guide](docs/installation.md).

2. **Configure GitHub token**

CIFTT requires a GitHub Personal Access Token to interact with the GitHub API.

**Create a token:**
1. Go to https://github.com/settings/tokens/new
2. Give it a descriptive name (e.g., "CIFTT CLI")
3. Select scopes:
   - ✅ `repo` (required for all operations)
   - ✅ `project` (required for `--project` and `--fields` options)
4. Click "Generate token" and copy it

**Provide the token to CIFTT:**

Option A - Export as environment variable (recommended):
```bash
export GITHUB_TOKEN=your_token_here
```

Option B - Using a `.env` file:
```bash
# Create .env file in the project root
echo "GITHUB_TOKEN=your_token_here" > .env
```

**Note:** Using environment variables is more secure as tokens aren't stored in plain text files on your system.

**For organizations with SSO:** After creating the token, you must authorize it for your organization. Click "Configure SSO" next to the token and authorize the organization.

3. **Verify your setup**
```bash
ciftt check-token
```

This will verify your token is valid and show your permissions.

## 🚀 Quick Start

```bash
# Check your GitHub token and permissions
ciftt check-token

# Create new issues from CSV
ciftt create-issues input.csv myorg/myrepo

# Update existing issues (basic fields only)
ciftt update-issues input.csv

# Update existing issues and their project fields from CSV
ciftt update-issues input.csv --project myorg/123

# Export issues to CSV
ciftt export-issues myorg/myrepo output.csv

# Export specific issues
ciftt export-issues myorg/myrepo output.csv --issues "1,3-5,8"

# Export all issues (including closed ones)
ciftt export-issues myorg/myrepo output.csv --all

# Export issues with GitHub Project fields
ciftt export-issues myorg/myrepo output.csv --fields "Priority,Status,Sprint"

# Export specific issues with project fields
ciftt export-issues myorg/myrepo output.csv --issues "1-10" --fields "Priority,Assignee,Due Date"

# Add issues to a GitHub Project v2 board
ciftt add-to-project issues.csv myorg/123
```

## 📄 File Format Support

CIFTT supports both **CSV** (Comma-Separated Values) and **TSV** (Tab-Separated Values) files as input. Simply provide the file path with the appropriate extension (`.csv` or `.tsv`) and CIFTT will automatically detect and parse the format correctly.

```bash
# CSV files
ciftt create-issues issues.csv myorg/myrepo
ciftt update-issues issues.csv --project myorg/123

# TSV files
ciftt create-issues issues.tsv myorg/myrepo
ciftt update-issues issues.tsv --project myorg/123
```

### Creating Issues
For creating new issues, your file should include headers like:
```csv
Title,Description,Labels,Assignee
```

**Note:** Column names are case-sensitive. Use proper case (Title, Description, etc.).

Only the `Title` column is mandatory to create an issue.

### Updating Issues
For updating existing issues, your file must include the `URL` column to identify which issues to update:
```csv
Title,Description,Labels,Assignee,URL
```

To also update GitHub Project v2 fields, add those columns and use the `--project` option:
```csv
Title,Description,Labels,Assignee,URL,Priority,Status,Sprint
```

**Note:** Column names are case-sensitive. Standard issue fields use proper case (Title, Description, Labels, Assignee, URL) while project field names match exactly as they appear in your GitHub Project.

- The `URL` column is **required** for updates (to identify which issue to update)
- Any additional columns beyond standard issue fields are treated as GitHub Project v2 fields
- Project fields are **only updated** when the `--project` option is provided
- A warning is shown if project field columns exist in the CSV but no `--project` is specified

**State Management:**
- The optional `State` column allows you to open or close issues
  - Accepted values: `open` or `closed`
  - Example: `State,URL` → `closed,https://github.com/owner/repo/issues/123`
- The optional `StateReason` column specifies why an issue was closed
  - Valid values: `completed` (default), `not_planned`, `duplicate`, or `reopened`
  - Only applies when `State` is `closed`
  - Example CSV: `State,StateReason,URL` → `closed,duplicate,https://github.com/...`

**Important: Labels are completely replaced, not merged**
- When you specify labels in your CSV, they **completely replace** the existing labels on the issue
- To preserve existing labels, include them in your CSV along with any new labels
- Example: If an issue has label `bug` and your CSV contains `"enhancement,ui"`, the result will be only `enhancement` and `ui` (the `bug` label will be removed)
- To keep all labels: Export issues first, edit the CSV to include both existing and new labels (e.g., `"bug,enhancement,ui"`), then update

**Format Notes:**
- CSV files use commas as separators: `Title,Description,URL`
- TSV files use tabs as separators: `Title	Description	URL`
- When exporting, CIFTT always outputs CSV format with newlines preserved as "\n" characters

## 🎯 GitHub Project v2 Integration

### Exporting with Project Fields
When using the `--fields` option during export, CIFTT will fetch GitHub Project v2 field values and include them as additional columns in your CSV:

```csv
Title,Description,Labels,Assignee,URL,Priority,Status,Sprint
"Fix login bug","User cannot login with special characters","bug,high-priority","john","https://github.com/myorg/myrepo/issues/42","High","In Progress","Sprint 23"
```

### Updating Project Fields
The `update-issues` command can update both standard issue fields and GitHub Project v2 fields. The `--project` option is **optional** and only required when you want to update project fields.

**Use cases:**
```bash
# Update only issue fields (title, description, labels, etc.) - no project needed
ciftt update-issues updated_issues.csv

# Update both issue fields AND project fields - requires --project option
ciftt update-issues updated_issues.csv --project owner/123
```

CIFTT automatically detects project field columns (any column that isn't a standard issue field). If project field columns are present in your CSV but you don't provide the `--project` option, CIFTT will show a warning and skip updating those fields.

**Supported project identifier formats:**
- Full URLs: `https://github.com/users/owner/projects/123`
- Full URLs: `https://github.com/orgs/myorg/projects/456`
- Short format: `owner/projects/123`
- Shortest format: `owner/123`

```bash
# Update issues and project fields using different identifier formats
ciftt update-issues updated_issues.csv --project owner/123
ciftt update-issues updated_issues.csv --project owner/projects/123
ciftt update-issues updated_issues.csv --project https://github.com/users/owner/projects/123

# Use short flag -p
ciftt update-issues updated_issues.csv -p owner/123
```

**Note:** Project field updates only work with `update-issues` (not `create-issues`) because newly created issues aren't immediately added to projects.

This allows you to export issues with their current project field values, modify them in your spreadsheet, and then re-import to update both the issues and their project fields.

### Adding Issues to Projects

The `add-to-project` command adds existing GitHub issues to a Project v2 board. This is useful when you have a list of issue URLs and want to bulk add them to a project.

**CSV Format:**
```csv
URL
https://github.com/owner/repo/issues/1
https://github.com/owner/repo/issues/2
https://github.com/owner/repo/issues/3
```

**Usage:**
```bash
# Add issues from CSV to a project
ciftt add-to-project issues.csv owner/123

# All project identifier formats are supported
ciftt add-to-project issues.csv owner/projects/123
ciftt add-to-project issues.csv https://github.com/orgs/owner/projects/123

# Dry-run to preview what will be added
ciftt add-to-project issues.csv owner/123 --dry-run
```

**Features:**
- Idempotent operation - safe to run multiple times (issues already in the project are skipped automatically by GitHub)
- Supports issues from multiple repositories in a single CSV
- Validates all issues exist and are accessible before adding
- Clear progress reporting for each issue added

## 🔐 Token Validation

Before importing or exporting issues, you can validate your GitHub token:

```bash
ciftt check-token
```

This command will:
- ✅ Verify your token is valid and show the authenticated user
- 🔑 Display your token's scopes (permissions)
- 🏢 List authorized organizations (helpful for SSO troubleshooting)
- 📊 Show current API rate limit status

Unlike simple CSV import scripts, CIFTT automatically validates that your token has the required scopes and can access the target repository/project at the beginning of operations. This prevents frustrating 403 errors and provides clear guidance when permissions are missing or SSO needs to be enabled for an organization.

**Required scopes:**
- `repo` scope - Required for all operations (creating, updating, and exporting issues)
- `project` scope - Only required when using `--project` option with `update-issues` or `--fields` option with `export-issues`

When using the `--project` option, CIFTT also validates that the specified GitHub Project exists and is accessible before processing any issues.

## 🤖 Disclaimer

CIFTT is experimental. Like your last relationship. Use with caution.
We’re not responsible for any emotional damage caused by accidental issue spam.
