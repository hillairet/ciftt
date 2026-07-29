# Exporting Issues

CIFTT exports GitHub issues from a repository to a CSV file that can be edited and used with `update-issues` or `add-to-project`.

## Basic Export

Export open issues from a repository:

```bash
ciftt export-issues owner/repo output.csv
```

The default CSV columns are:

```csv
Title,Description,Labels,Assignee,URL
```

Descriptions are exported with newlines preserved as `\n` characters so each issue stays on one CSV row.

## Selecting Issues

Export specific issues by number:

```bash
ciftt export-issues owner/repo output.csv --issues "1,3-5,8"
```

Export open and closed issues:

```bash
ciftt export-issues owner/repo output.csv --all
```

If neither `--issues` nor `--all` is provided, CIFTT exports open issues only.

## Exporting GitHub Project V2 Fields

Use `--fields` to include GitHub Project v2 field values in the CSV:

```bash
ciftt export-issues owner/repo output.csv --fields "Priority,Status,Sprint"
```

This produces a CSV with the standard issue columns plus one column for each requested project field:

```csv
Title,Description,Labels,Assignee,URL,Priority,Status,Sprint
"Fix login bug","User cannot login with special characters","bug,high-priority","john","https://github.com/owner/repo/issues/42","High","In Progress","Sprint 23"
```

Project field names are exact and case-sensitive. The `--fields` option requires a GitHub token with the `project` scope.

## How Project Field Export Works

Export is repository-based, not project-based.

There is currently no `--project` option for `export-issues`. When `--fields` is provided, CIFTT fetches each issue from the repository and then asks GitHub for the Project v2 items attached to that issue. CIFTT looks through those project items and extracts values whose field names match the requested names.

This has a few important consequences:

- If an issue has the requested field in one of its projects, the value is exported.
- If an issue does not have the requested field, the CSV value is blank.
- If different projects use different field names, request the union of fields you care about.
- If multiple projects have a field with the same name, CIFTT does not distinguish which project the value came from.
- If a field exists in the source project but not in the target project, export still succeeds, but update into the target project will not be able to set that field.

For example, if some issues use `Priority` and others use `Impact`, export both fields:

```bash
ciftt export-issues owner/repo output.csv --fields "Priority,Impact,Status,Sprint"
```

Rows for issues without `Priority` will have an empty `Priority` value. Rows for issues without `Impact` will have an empty `Impact` value.

## Transferring Issues Between Projects

A common transfer workflow is:

```bash
ciftt export-issues owner/repo issues.csv --fields "Priority,Status,Sprint"
ciftt add-to-project issues.csv target-owner/123
ciftt update-issues issues.csv --project target-owner/123
```

The first command exports issue data and selected project fields. The second command adds those existing issues to the target GitHub Project v2 board. The third command updates the target project's fields from the CSV columns.

## Transfer Caveats

Before transferring between projects, check these details:

- Target project fields must already exist.
- Target project field names must match the CSV column names exactly.
- Single-select values in the CSV must already exist as options in the target project.
- CIFTT does not remap field names between source and target projects.
- CIFTT does not currently filter export values to one specified source project.
- Project field export is ambiguous when multiple source projects have fields with the same name.

If the source and target projects use different field names, edit the CSV headers before running `update-issues`.

## Limitations

Current export behavior has these limits:

- `export-issues` exports from one repository at a time.
- `export-issues` cannot currently select a specific source project.
- Project field names are matched by exact field name only.
- Duplicate field names across projects are not disambiguated.
- The GraphQL query currently reads up to 10 project items per issue and up to 20 field values per project item.
