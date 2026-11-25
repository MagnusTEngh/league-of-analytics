#!/usr/bin/env bash
set -euo pipefail

echo "Running ruff-format..."
ruff format .
