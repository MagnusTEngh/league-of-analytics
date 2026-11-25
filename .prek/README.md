# Prek Hooks

This directory contains Prek configuration and hooks for the project.

## Usage

Run all hooks:
```bash
prek run
```

Run specific stage:
```bash
prek run --stage always
```

Run specific hook:
```bash
prek run --hook <hook-id>
```

## Configuration

The `prek.yaml` file is generated based on the selected components. Hooks are only included if their corresponding component is active.

## GitHub Actions

Each hook can be run individually in GitHub workflows. See `.github/workflows/prek.yml` for the workflow configuration.
