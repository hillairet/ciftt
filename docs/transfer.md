# Transferring Issues

CIFTT can transfer existing GitHub issues into another repository with GitHub's issue transfer API.

```bash
ciftt transfer-issues exported.csv transferred.csv target-owner/target-repo
```

The input file must contain a `URL` column with GitHub issue URLs. Pull request URLs are skipped. The output file keeps the input rows, removes `Assignee`, and rewrites `URL` to the destination issue URL.

If `Description` is present, CIFTT patches the destination issue body after transfer so the CSV description is preserved.

Closed source issues are temporarily reopened because GitHub requires open issues for transfer. CIFTT comments on the source issue, reopens it, transfers it, and closes the destination issue with the same close reason when GitHub provides one (`completed`, `not_planned`, or `duplicate`).

If the input file contains `StateReason`, CIFTT uses it as an explicit override when reclosing transferred issues. This is useful when you need to correct or audit close reasons in the transfer CSV. Valid transfer close reasons are `completed`, `not_planned`, and `duplicate`.

To stop after a small batch:

```bash
ciftt transfer-issues exported.csv transferred.csv target-owner/target-repo --limit 10
```

If `transferred.csv` already exists, CIFTT uses existing destination URLs in that file to skip rows that were already transferred.

## Full Project Restore Workflow

When exporting issues as the source for a transfer, include a `StateReason` column when possible. `transfer-issues` can query the source issue close reason directly, but keeping `StateReason` in the CSV makes the intended close reason visible and gives you an explicit override if GitHub's queried value is missing or needs correction.

```bash
ciftt export-issues source-owner/source-repo exported.csv --all --fields "Priority,Status,Sprint"
ciftt transfer-issues exported.csv transferred.csv target-owner/target-repo
ciftt add-to-project transferred.csv project-owner/123
ciftt update-issues transferred.csv --project project-owner/123
```

`transfer-issues` does not add issues to projects and does not restore Project v2 field values. Use `add-to-project` and `update-issues` after transfer.
