#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="${SCRIPT_DIR}/install_plugin.py"

if command -v uv >/dev/null 2>&1; then
  exec uv run python "${PYTHON_SCRIPT}" "$@"
fi

if command -v python3 >/dev/null 2>&1; then
  exec python3 "${PYTHON_SCRIPT}" "$@"
fi

exec python "${PYTHON_SCRIPT}" "$@"
