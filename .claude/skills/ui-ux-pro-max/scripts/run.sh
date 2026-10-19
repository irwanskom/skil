#!/usr/bin/env bash
# Cross-platform launcher for search.py (Linux, macOS, Windows Git Bash).
# Picks the first working Python 3: the Windows "py" launcher first, then
# python, then python3. The Microsoft Store "python" stub fails the check.
set -u
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8

for cand in "py -3" python python3; do
  if $cand -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" >/dev/null 2>&1; then
    exec $cand "$DIR/search.py" "$@"
  fi
done

echo "ui-ux-pro-max: Python 3.8+ not found." >&2
echo "Windows: winget install Python.Python.3.12  (or https://www.python.org/downloads/windows/ and tick 'Add python.exe to PATH')" >&2
exit 127
