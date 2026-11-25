#!/usr/bin/env python3
"""Generate a Quarto markdown page from coverage.json."""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def get_git_sha() -> str:
    """Get git commit SHA from environment or git command."""
    sha = os.environ.get("GITHUB_SHA")
    if sha:
        return sha[:8]

    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()[:8]
    except Exception:
        return "unknown"


def get_fail_under() -> int:
    """Read fail_under value from pyproject.toml."""
    try:
        import tomllib

        with open("pyproject.toml", "rb") as f:
            config = tomllib.load(f)
        return config.get("tool", {}).get("coverage", {}).get("report", {}).get("fail_under", 80)
    except Exception:
        return 80


def main() -> None:
    """Generate coverage.qmd from coverage.json."""
    coverage_json_path = Path("coverage.json")
    output_path = Path("docs/coverage.qmd")

    if not coverage_json_path.exists():
        print("Error: coverage.json not found. Run 'uv run coverage json' first.")
        sys.exit(1)

    with open(coverage_json_path) as f:
        data = json.load(f)

    totals = data.get("totals", {})
    total_percent = totals.get("percent_covered", 0)
    total_covered = totals.get("covered_lines", 0)
    total_lines = totals.get("num_statements", 0)

    fail_under = get_fail_under()
    meets_threshold = total_percent >= fail_under

    git_sha = get_git_sha()
    date = datetime.now().strftime("%Y-%m-%d")

    # Build file rows
    file_rows = []
    files = data.get("files", {})
    for path, file_data in sorted(
        files.items(), key=lambda x: x[1].get("summary", {}).get("percent_covered", 0)
    ):
        summary = file_data.get("summary", {})
        percent = summary.get("percent_covered", 0)
        covered = summary.get("covered_lines", 0)
        missing = len(file_data.get("missing_lines", []))
        total = covered + missing
        file_rows.append(
            f"| [{path}]({path}) | {covered}/{total} | {missing} | {percent:.1f}% |"
        )

    file_table = "\n".join(file_rows) if file_rows else "No file data available"

    check_mark = "\u2705" if meets_threshold else "\u274c"

    content = f"""---\ntitle: Test Coverage\noader: last\n---\n\n# Test Coverage\n\nGenerated from commit `{git_sha}` on {date}.\n\n## Summary\n\n- **Total Coverage**: {total_percent:.1f}%\n- **Statements**: {total_covered}/{total_lines} covered\n- **Threshold**: {fail_under}% {check_mark} Met\n\n## File Coverage\n\n| File | Statements | Missing | Coverage |\n|------|------------|---------|----------|\n{file_table}\n\n## Full Report\n\nView the [full interactive HTML report](../coverage/index.html).\n"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(content)

    print(f"Generated {output_path}")


if __name__ == "__main__":
    main()
