#!/bin/bash
set -e
cd "$(dirname "$0")"
if [ -x .venv/bin/python ]; then
    PYTHON_BIN="$PWD/.venv/bin/python"
elif [ -x venv/bin/python ]; then
    PYTHON_BIN="$PWD/venv/bin/python"
else
    echo "Run ./install.sh first to install Clip Assassin."
    exit 1
fi
exec "$PYTHON_BIN" launch.py
