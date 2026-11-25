# AGENTS.md

Goal: gather League of Legends data from the Riot Games API and present a data science dashboard, published as a web app.

## Sources of truth

Read before starting any task:

- `README.md`: project overview
- `docs/architecture/00_overview.qmd`: structure and data flow

**Do not edit `README.md` or `docs/architecture/` directly.** No direct commits, no pushes to the main branch.

If you think one needs a change, open a pull request containing only that change, with a short description of what and why. A human reviews and merges it. Never bundle these edits into a PR with code changes.

## Conventions

- Keep code simple and readable; prefer clarity over cleverness.
- Keep responses and explanations brief.
- Python, managed with `uv`.
- Dev environment managed with nix.
- Type hints and short docstrings, matching existing style.

## Don'ts

- Never commit API keys or anything under `data/`.
- Don't change the architecture.
- Don't add dependencies without saying why.

## Roles

Load the matching skill from `.agents/skills/`:

- `leader`: plans and delegates
- `worker`: implements one issue
- `reviewer`: reviews one change, read-only
- `curator`: audits and updates docs/

## Context

- Before starting a task, check `docs/00_index.qmd` for relevant project documentation
- When navigating docs/ always check a folders README.md first to find which files are relevant
- Consult additional documentation selectively, focusing only on information relevant to the current task
- Prefer existing documentation over assumptions when determining project conventions, architecture, and workflows
- If documentation is missing, outdated, or inconsistent with the codebase, take note and update it when appropriate
- If a change introduces a significant architectural decision, propose a new ADR in `docs/architecture/decisions/`

## Rules

- Follow `.gitmessage` when making commits
- Follow `docs/01_rules.qmd` when changing docs/ content
