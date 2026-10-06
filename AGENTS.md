# AGENTS.md

Goal: gather League of Legends data from the Riot Games API and present a data science dashboard, published as a web app.

## Sources of truth

Read before starting any task:

- `README.md`: project overview
- `architecture.md`: structure and data flow

**Do not edit `README.md` or `architecture.md` directly.** No direct commits, no pushes to the main branch.

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