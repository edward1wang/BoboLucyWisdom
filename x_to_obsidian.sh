#!/bin/bash
# x_to_obsidian.sh - Wrapper script that always uses the venv
VENV_PATH="${HOME}/.venvs/xscraper"
SCRIPT="${HOME}/workspace/x_to_obsidian.py"

# Ensure venv exists
if [ ! -d "$VENV_PATH" ]; then
    echo "Virtual environment not found. Creating..."
    mkdir -p "$(dirname "$VENV_PATH")"
    python3 -m venv "$VENV_PATH"
    "$VENV_PATH/bin/pip" install twscrape --quiet
fi

# Activate and run
source "$VENV_PATH/bin/activate"
exec python3 "$SCRIPT" "$@"