# Importing and Updating Issues

CIFTT can create issues, update existing issues, add existing issues to GitHub Project v2 boards, and update Project v2 field values from CSV or TSV files.

## File Format

CIFTT supports CSV and TSV input files. The file extension determines how the file is parsed:

- `.csv` files use commas.
- `.tsv` files use tabs.

Column names are case-sensitive.

## Creating Issues

Create new issues from a file:

```bash
ciftt create-issues issues.csv owner/repo
```

The `Title` column is required. Other standard columns are optional:

```csv
Title,Description,Labels,Assignee
"Fix login bug","User cannot login with special characters","bug,high-priority","john"
```

Project fields are not set by `create-issues`. To set Project v2 fields, first create the issues, add them to a project, then run `update-issues` with `--project`.

## Updating Existing Issues

Update existing issues from a file:

```bash
ciftt update-issues issues.csv
```

The `URL` column is required because it identifies which issue to update:

```csv
Title,Description,Labels,Assignee,URL
"Fix login bug","Updated description","bug,high-priority","john","https://github.com/owner/repo/issues/42"
```

Standard issue columns are:

- `Title`
- `Description`
- `Labels`
- `Assignee`
- `URL`
- `State`
- `StateReason`

## State Management

Use `State` to open or close issues:

```csv
State,URL
closed,https://github.com/owner/repo/issues/42
```

Accepted `State` values are `open` and `closed`.

Use `StateReason` when closing an issue:

```csv
State,StateReason,URL
closed,duplicate,https://github.com/owner/repo/issues/42
```

Valid `StateReason` values are `completed`, `not_planned`, `duplicate`, and `reopened`.

## Label Replacement

Labels are replaced, not merged.

If an issue currently has `bug` and the CSV contains `enhancement,ui`, the issue will end up with only `enhancement` and `ui`. To preserve existing labels, include them in the CSV with any new labels:

```csv
Labels,URL
"bug,enhancement,ui",https://github.com/owner/repo/issues/42
```

## Updating Project Fields

Use `--project` to update GitHub Project v2 fields:

```bash
ciftt update-issues issues.csv --project owner/123
```

Any column that is not a standard issue column is treated as a Project v2 field:

```csv
Title,Description,Labels,Assignee,URL,Priority,Status,Sprint
"Fix login bug","Updated description","bug,high-priority","john","https://github.com/owner/repo/issues/42","High","In Progress","Sprint 23"
```

Project field names must match the target project's field names exactly. The `--project` option requires a GitHub token with the `project` scope.

If project field columns are present but `--project` is not provided, CIFTT updates the standard issue fields and skips the project fields.

## Supported Project Identifiers

The `--project` option accepts these formats:

```bash
ciftt update-issues issues.csv --project owner/123
ciftt update-issues issues.csv --project owner/projects/123
ciftt update-issues issues.csv --project https://github.com/users/owner/projects/123
ciftt update-issues issues.csv --project https://github.com/orgs/owner/projects/123
```

The short flag is also supported:

```bash
ciftt update-issues issues.csv -p owner/123
```

## Adding Existing Issues To A Project

Use `add-to-project` when you already have GitHub issues and want to bulk add them to a Project v2 board:

```bash
ciftt add-to-project issues.csv owner/123
```

The CSV only needs issue URLs:

```csv
URL
https://github.com/owner/repo/issues/1
https://github.com/owner/repo/issues/2
https://github.com/another-repo/example/issues/3
```

Preview the operation without changing GitHub:

```bash
ciftt add-to-project issues.csv owner/123 --dry-run
```

`add-to-project` supports issues from multiple repositories in one CSV. GitHub skips issues that are already in the project, so the command is safe to run multiple times.

## Transfer Workflow

To transfer existing issues and selected Project v2 fields from one project to another:

```bash
ciftt export-issues owner/repo issues.csv --fields "Priority,Status,Sprint"
ciftt add-to-project issues.csv target-owner/123
ciftt update-issues issues.csv --project target-owner/123
```

Review [Exporting Issues](export.md) for details about how project field export behaves when issues belong to multiple projects.
