#!/usr/bin/env python3
"""
CIFTT - CSV Input for Feature Triage and Tracking
A tool to create or update GitHub issues from CSV input.
"""
import pandas as pd
import typer

from commands.export_issues import export_issues
from commands.import_issues import import_issues

app = typer.Typer(help="CIFTT - CSV Input for Feature Triage and Tracking")

app.command()(import_issues)
app.command()(export_issues)


if __name__ == "__main__":
    app()
