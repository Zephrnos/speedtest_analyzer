# Network Topology & Latency Audit

This repository contains a suite of tools designed to audit local network performance, specifically focusing on hop-by-hop latency (MTR) and ISP throughput stability.

The goal of this project is to collect comparative data to isolate building-level infrastructure issues from unit-level hardware faults.

## Privacy & Safety
**This tool is designed with strict privacy in mind.**
* **No Traffic Logging:** This tool **does not** sniff packets, log DNS queries, or record browsing history.
* **No PII:** No personal identifiable information is collected.
* **What IS Collected:**
    * `fast.com` speed metrics (Download/Upload/Latency/Bufferbloat).
    * `mtr` (My Traceroute) statistics for the route to `8.8.8.8`.

## Project Structure
* `run_audit.sh`: The core data collection script (Bash).
* `speed_grapher.py` / `mtr_grapher.py`: Visualization tools (Python).
* `analyzer`: A Rust utility for statistical outlier detection.

## Prerequisites

* **Node.js** (for the `fast-cli` speedtest client)
* **Python 3.8+** (for visualization)
* **Rust** (optional, for the analyzer tool)
* **MTR** (`sudo apt install mtr` or equivalent)

## Installation

1.  **Install the Speedtest Client:**
    ```bash
    npm install --global fast-cli
    ```

2.  **Install Python Dependencies:**
    It is recommended to use a virtual environment.
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

3.  **Build the Analyzer (Optional):**
    ```bash
    cargo build --release
    ```

## Usage: Data Collection

The `run_audit.sh` script is designed to run via `cron` or a systemd timer. It automatically detects your environment paths.

**Manual Run:**
```bash
./run_audit.sh
```

**Scheduled Run (Crontab Example)**
    Run a full audit every hour, and a lightweight MTR trace every minute.
    ```bash
    # Open crontab
    crontab -e

    # Add these lines (Adjust paths as necessary)
    # Run MTR trace every minute
    * * * * * /path/to/repo/run_audit.sh --mtr

    # Run Speedtest every hour
    0 * * * * /path/to/repo/run_audit.sh --speed
    ```

## Usage: Visualization

To generate graphs from the collected logs:

```bash
# Generate Speedtest Graphs
python3 speed_grapher.py

# Generate MTR Latency Graphs
python3 mtr_grapher.py
```
