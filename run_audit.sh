#!/bin/bash

# --- Dynamic Configuration ---
# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
LOG_DIR="$SCRIPT_DIR/logs"

# Ensure log directories exist
MTR_SUBDIR="$LOG_DIR/mtr_logs"
SPEED_SUBDIR="$LOG_DIR/speed_tests"
mkdir -p "$MTR_SUBDIR" "$SPEED_SUBDIR"

# Timestamps
TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
FULL_DATE=$(date +%Y-%m-%d)
ERROR_LOG="$LOG_DIR/error.log"

# Path detection for binaries
# This attempts to find 'fast' and 'mtr' in the user's path automatically
FAST_CMD=$(which fast)
MTR_CMD=$(which mtr)

# --- Functions ---

run_mtr() {
    if [ -z "$MTR_CMD" ]; then
        echo "$(date): MTR command not found. Please install mtr." >> "$ERROR_LOG"
        exit 1
    fi
    
    MTR_FILE="$MTR_SUBDIR/mtr_report-$TIMESTAMP.txt"
    # -r: Report, -c 10: 10 packets, -n: No DNS (faster/privacy), -w: Wide
    $MTR_CMD -r -c 10 -n -w 8.8.8.8 > "$MTR_FILE" 2>> "$ERROR_LOG"
}

run_speedtest() {
    if [ -z "$FAST_CMD" ]; then
        echo "$(date): 'fast' command not found. Run 'npm install --global fast-cli'" >> "$ERROR_LOG"
        exit 1
    fi

    SPEED_FILE="$SPEED_SUBDIR/speedtest-$TIMESTAMP.json"
    # Run the heavy download test
    $FAST_CMD --upload --json > "$SPEED_FILE" 2>> "$ERROR_LOG"
}

# --- Execution Logic ---

# Check for arguments to decide what to run
if [[ "$1" == "--mtr" ]]; then
    run_mtr
elif [[ "$1" == "--speed" ]]; then
    run_speedtest
elif [[ "$1" == "--all" ]]; then
    run_mtr
    run_speedtest
else
    echo "Usage: $0 {--mtr|--speed|--all}"
    echo "  --mtr   : Run only the trace route (lightweight)"
    echo "  --speed : Run the bandwidth test (heavy)"
    echo "  --all   : Run both"
    exit 1
fi