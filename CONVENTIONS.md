# CIFTT Development Conventions

CIFTT is a simple Python script providing a CLI to create or update issues in GitHub using a CSV input.

## General requirements

Use the following packages:

* typer for the CLI
* pydantic for clients and data classes
* pydantic-settings for the settings

I use the following formatter and linter so respect their requirements:

* flake8
* black
* isort

## Structure

The main script is in the root along with the supporting modules:

```bash
ciftt/
|-- ciftt.py
|-- settings.py
|-- csv_data.py
|-- github/
|   |-- __init__.py
|   |-- client.py
|   |-- project.py
|   |-- issue.py
|-- utils/
|   |-- __init__.py
|   |-- validators.py
|-- requirements.txt
|-- README.md
```

## Version Control

DO NOT USE CONVENTIONAL COMMITS.
Use gitmojis for the git commits instead:

* Use :sparkles: for features
* Use :recycle: for refactor
* Use :bug: for a fix
