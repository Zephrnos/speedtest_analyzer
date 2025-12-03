#!/bin/bash

# --- Configuration ---
export PATH=/home/zephrnos/.nvm/versions/node/v20.19.5/bin:/usr/bin:/bin
FAST_CMD="/home/zephrnos/.nvm/versions/node/v20.19.5/bin/fast"
MTR_CMD="/usr/bin/mtr"

# 1. BASE LOG DIRECTORY (Change this if needed)
LOG_DIR="/home/zephrnos/Throttle_tests"

# 2. DEFINE SUBDIRECTORIES
MTR_SUBDIR="$LOG_DIR/mtr_logs"
SPEED_SUBDIR="$LOG_DIR/speed_tests"

# Timestamps
FULL_DATE=$(date +%Y-%m-%d)
TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
CURRENT_MINUTE=$(date +%M)

# 3. DEFINE FINAL FILE PATHS
# Primary Log (still goes to base folder)
LATENCY_LOG="$LOG_DIR/latency_log_$FULL_DATE.csv"
ERROR_LOG="$LOG_DIR/cron_errors.log"
# MTR file now points to the subdirectory
MTR_FILE="$MTR_SUBDIR/mtr_report-$TIMESTAMP.txt"

# Ensure ALL directories exist (Base + Subdirs)
mkdir -p "$LOG_DIR" "$MTR_SUBDIR" "$SPEED_SUBDIR"

# ==========================================
# PART 1: HIGH-FREQUENCY LOGGING (Every Minute)
# ==========================================

# A. Ping Logger (Latency & Packet Loss)
# ... (This section remains unchanged) ...

# B. MTR (Trace Path)
# Runs a quick trace to save to its own unique file in the mtr_logs subdirectory.
if [ -x "$MTR_CMD" ]; then
    echo "--- MTR Report: $TIMESTAMP ---" > "$MTR_FILE"
    # -r: Report mode, -c 10: 10 packets, -n: No DNS (faster), -w: Wide output
    $MTR_CMD -r -c 10 -n -w 8.8.8.8 >> "$MTR_FILE" 2>> "$ERROR_LOG"
fi

# ==========================================
# PART 2: HEAVY SPEED TEST (Hourly Only)
# ==========================================

# Only run this if the current minute is exactly "00"
if [ "$CURRENT_MINUTE" == "00" ]; then
    # Speedtest JSON file now points to the speed_tests subdirectory
    SPEED_FILE="$SPEED_SUBDIR/speedtest-$TIMESTAMP.json"

    # Run the heavy download test
    $FAST_CMD --upload --json > "$SPEED_FILE" 2>> "$ERROR_LOG"
fi