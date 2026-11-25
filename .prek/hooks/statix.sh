#!/usr/bin/env bash
set -euo pipefail

echo "Running statix..."
statix check
