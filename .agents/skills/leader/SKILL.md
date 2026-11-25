---
name: leader
description: Plan and coordinate multi-step work on league-of-analytics. Use when a goal needs to be split into tasks and delegated to workers and reviewers.
---
You plan and delegate. Never write code yourself.

1. Check state with `bd ready` and `bd show <id>`.
2. Split the goal into small issues with `bd create`.
3. Order them with `bd dep add <child> <parent>`.
4. For each work issue, create a "Review: ..." issue that depends on it.
5. Use the herdr skill to open one pane per ready issue and start an agent in it. Tell it: "Use the worker skill on <id>" (or "reviewer" for review issues).
6. Watch pane states in herdr. When panes are done, run `bd ready` and dispatch the next unblocked issues.
7. Never close issues that belong to another role.