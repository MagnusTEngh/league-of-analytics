---
name: worker
description: Implement a single beads issue. Use when assigned an issue id to build or fix.
---
1. Run `bd show <id>`, then `bd update <id> --claim`.
2. Implement exactly that issue, nothing more.
3. If you find extra work, file it with `bd create` instead of doing it.
4. Finish with `bd close <id> "what you changed"`.