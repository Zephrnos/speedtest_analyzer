#!/bin/bash

# --- Configuration ---
# Set the PATH for nvm/node
export PATH=/home/zephrnos/.nvm/versions/node/v20.19.5/bin:/usr/bin:/bin

# Directory to save files
LOG_DIR="/home/zephrnos/Speedtests"

# Path to commands
FAST_CMD="/home/zephrnos/.nvm/versions/node/v20.19.5/bin/fast"
MTR_CMD="/usr/bin/mtr"
# --- End Configuration ---

# 1. Create the file names
TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
JSON_FILE="$LOG_DIR/speedtest-$TIMESTAMP.json"
MTR_FILE="$LOG_DIR/mtr-$TIMESTAMP.txt"
ERROR_LOG="$LOG_DIR/cron_errors.log"

# 2. Run the Speedtest
#    Redirects output to JSON file, errors to the timestamped error log
$FAST_CMD --upload --json > "$JSON_FILE" 2> >(awk '{ print strftime("%Y-%m-%d %H:%M:%S - "), $0; fflush() }' >> "$ERROR_LOG")

# 3. Run MTR (My Traceroute)
#    -r : Report mode (outputs text table)
#    -c 20 : Count 20 packets (good sample size)
#    -w : Wide report (doesn't cut off long hostnames)
#    -n : No DNS resolution (OPTIONAL: remove -n if you want to see hostnames like "fidium.net")
#    We target 8.8.8.8 (Google) to test the path to the internet
if [ -x "$MTR_CMD" ]; then
    echo "--- MTR Report for $TIMESTAMP ---" > "$MTR_FILE"
    $MTR_CMD -r -c 20 -w 8.8.8.8 >> "$MTR_FILE" 2>> "$ERROR_LOG"
else
    echo "$(date +'%Y-%m-%d %H:%M:%S') - MTR command not found or executable" >> "$ERROR_LOG"
fi
