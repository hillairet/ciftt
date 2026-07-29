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

## 📚 Guides

- [Installation](docs/installation.md): install CIFTT, run it with `uvx`, or set up a development checkout.
- [Exporting issues](docs/export.md): export repository issues to CSV, include GitHub Project v2 fields, and understand behavior when issues belong to multiple projects.
- [Importing and updating issues](docs/import.md): create issues, update existing issues, add issues to projects, and update Project v2 fields from CSV or TSV files.

## 📄 File Format Support

CIFTT supports CSV and TSV input files. Column names are case-sensitive.

For creating issues, `Title` is required:

```csv
Title,Description,Labels,Assignee
```

For updating issues, `URL` is required:

```csv
Title,Description,Labels,Assignee,URL
```

For Project v2 field updates, add project field columns and use `--project`:

```csv
Title,Description,Labels,Assignee,URL,Priority,Status,Sprint
```

See [Importing and Updating Issues](docs/import.md) for state management, label replacement behavior, project field updates, and `add-to-project` usage.

## 🎯 GitHub Project v2 Integration

CIFTT can export selected Project v2 fields with `--fields`, update target project fields with `--project`, and bulk add existing issues to a project with `add-to-project`.

Project field export is repository-based, not project-based. If issues belong to multiple projects, CIFTT extracts requested fields by exact field name from the project items attached to each issue. See [Exporting Issues](docs/export.md) for the full behavior and transfer caveats.

Supported project identifier formats include `owner/123`, `owner/projects/123`, and full GitHub project URLs.

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
