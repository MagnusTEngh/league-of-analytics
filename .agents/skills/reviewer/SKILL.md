---
name: reviewer
description: Review the change behind a "Review:" beads issue. Read-only; use when assigned a review issue id.
---
1. Run `bd show <id>`, then `bd update <id> --claim`.
2. Review the linked work for correctness and style. Do not edit files.
3. Approved: `bd close <id> "approved"`.
4. Problems: `bd create "Fix: ..."`, then `bd close <id> "changes requested: <fix-id>"`.