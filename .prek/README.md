# Prek Hooks

This directory contains hook scripts used by the pre-commit configuration.

## Usage

Run all hooks:

```bash
prek run -a
```

Run hooks for one component:

```bash
prek run -a --group nix
```

Run a single hook:

```bash
prek run -a nixfmt
```

## Configuration

The configuration lives in `.pre-commit-config.yaml` at the project root. Hooks are only included if their corresponding component is active.

## GitHub Actions

Each hook can be run individually in GitHub workflows. See `.github/workflows/` for the workflow configuration.
