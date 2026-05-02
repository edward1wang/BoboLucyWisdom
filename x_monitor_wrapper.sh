#!/bin/bash
# x_monitor_wrapper.sh - Run Playwright with proper venv
VENV="${HOME}/.venvs/xmonitor"
SCRIPT="${HOME}/workspace/x_playwright_monitor.py"

# Ensure venv exists
if [ ! -d "$VENV" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV"
fi

# Install requirements if needed
if ! "$VENV/bin/python" -c "import playwright" 2>/dev/null; then
    echo "Installing playwright..."
    "$VENV/bin/pip" install playwright
    "$VENV/bin/python" -m playwright install chromium
fi

# Run with activated venv
exec "$VENV/bin/python" "$SCRIPT" "$@"