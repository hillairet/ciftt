#!/usr/bin/env python3
"""
CIFTT - CSV Input for Feature Triage and Tracking
A tool to create or update GitHub issues from CSV input.
"""
import typer

from cli import check_token, create_issues, export_issues, update_issues
from cli.create_comments import create_comments

app = typer.Typer(help="CIFTT - CSV Input for Feature Triage and Tracking")

app.command()(create_issues)
app.command()(create_comments)
app.command()(update_issues)
app.command()(export_issues)
app.command()(check_token)


if __name__ == "__main__":
    app()
