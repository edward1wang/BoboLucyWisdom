#!/bin/bash
# x_cron_wrapper.sh
# Wrapper script for cron jobs with logging

USER="${1:-elonmusk}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${HOME}/.config/x_to_obsidian/cron.log"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Log with timestamp
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting scrape for @${USER}" >> "$LOG_FILE"

# Run the scraper
python3 "${SCRIPT_DIR}/x_to_obsidian.py" --user "$USER" --incremental >> "$LOG_FILE" 2>&1

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✓ Success" >> "$LOG_FILE"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✗ Failed (exit $EXIT_CODE)" >> "$LOG_FILE"
fi

echo "---" >> "$LOG_FILE"

exit $EXIT_CODE