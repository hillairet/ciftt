#!/usr/bin/env python3
"""
CIFTT - CSV Input for Feature Triage and Tracking
A tool to create or update GitHub issues from CSV input.
"""
import pandas as pd
import typer

from cli import export_issues, create_issues, update_issues, check_token

app = typer.Typer(help="CIFTT - CSV Input for Feature Triage and Tracking")

app.command()(create_issues)
app.command()(update_issues)
app.command()(export_issues)
app.command()(check_token)


if __name__ == "__main__":
    app()
