#!/usr/bin/env bash
set -euo pipefail

echo "Running ruff..."
ruff check .
