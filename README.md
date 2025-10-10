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

## 🚀 Quick Start

```bash
# Clone the repo
git clone https://github.com/hillairet/ciftt.git
cd ciftt

# Check your GitHub token and permissions
python ciftt.py check-token

# Create new issues from CSV
python ciftt.py create-issues input.csv myorg/myrepo

# Update existing issues (basic fields only)
python ciftt.py update-issues input.csv

# Update existing issues and their project fields from CSV
python ciftt.py update-issues input.csv --project myorg/123

# Export issues to CSV
python ciftt.py export-issues myorg/myrepo output.csv

# Export specific issues
python ciftt.py export-issues myorg/myrepo output.csv --issues "1,3-5,8"

# Export all issues (including closed ones)
python ciftt.py export-issues myorg/myrepo output.csv --all

# Export issues with GitHub Project fields
python ciftt.py export-issues myorg/myrepo output.csv --fields "Priority,Status,Sprint"

# Export specific issues with project fields
python ciftt.py export-issues myorg/myrepo output.csv --issues "1-10" --fields "Priority,Assignee,Due Date"
```

## 📄 File Format Support

CIFTT supports both **CSV** (Comma-Separated Values) and **TSV** (Tab-Separated Values) files as input. Simply provide the file path with the appropriate extension (`.csv` or `.tsv`) and CIFTT will automatically detect and parse the format correctly.

```bash
# CSV files
python ciftt.py create-issues issues.csv myorg/myrepo
python ciftt.py update-issues issues.csv --project myorg/123

# TSV files
python ciftt.py create-issues issues.tsv myorg/myrepo
python ciftt.py update-issues issues.tsv --project myorg/123
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
python ciftt.py update-issues updated_issues.csv

# Update both issue fields AND project fields - requires --project option
python ciftt.py update-issues updated_issues.csv --project owner/123
```

CIFTT automatically detects project field columns (any column that isn't a standard issue field). If project field columns are present in your CSV but you don't provide the `--project` option, CIFTT will show a warning and skip updating those fields.

**Supported project identifier formats:**
- Full URLs: `https://github.com/users/owner/projects/123`
- Full URLs: `https://github.com/orgs/myorg/projects/456`
- Short format: `owner/projects/123`
- Shortest format: `owner/123`

```bash
# Update issues and project fields using different identifier formats
python ciftt.py update-issues updated_issues.csv --project owner/123
python ciftt.py update-issues updated_issues.csv --project owner/projects/123
python ciftt.py update-issues updated_issues.csv --project https://github.com/users/owner/projects/123

# Use short flag -p
python ciftt.py update-issues updated_issues.csv -p owner/123
```

**Note:** Project field updates only work with `update-issues` (not `create-issues`) because newly created issues aren't immediately added to projects.

This allows you to export issues with their current project field values, modify them in your spreadsheet, and then re-import to update both the issues and their project fields.

## 🔐 Token Validation

Before importing or exporting issues, you can validate your GitHub token:

```bash
python ciftt.py check-token
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
