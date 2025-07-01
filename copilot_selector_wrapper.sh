#!/bin/bash
# Bash wrapper for copilot selector with FIFO output separation
# Based on Stack Overflow solution for curses GUI with redirected output

set -e

# Check arguments
if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <copilot_json_file>" >&2
    exit 1
fi

COPILOT_JSON_FILE="$1"

# Create a FIFO pipe for output
# Add timestamp and username to avoid conflicts
FIFO_PATH="/tmp/copilot_selector_fifo_$(whoami)_$(date +%H-%M-%S-%N)"

# Create FIFO if it doesn't exist
[ ! -p "$FIFO_PATH" ] && mkfifo "$FIFO_PATH"

# Function to cleanup FIFO on exit
cleanup() {
    rm -f "$FIFO_PATH"
}
trap cleanup EXIT

# Run the Python script in background with:
# - stdin/stdout redirected to current TTY (for curses interface)
# - FIFO path passed as argument for JSON output
uv run python select_copilots_interactive.py "$FIFO_PATH" "$COPILOT_JSON_FILE" >/dev/tty </dev/tty &

# Capture the process ID
PYTHON_PID=$!

# Read the JSON output from FIFO and write to stdout
# This allows the calling script to capture just the JSON result
cat "$FIFO_PATH"

# Wait for the Python process to complete
wait $PYTHON_PID

# Cleanup is handled by trap 