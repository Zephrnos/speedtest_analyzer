#!/usr/bin/env python3
"""
Generates clean, professional network graphs in PNG format.
Packet Loss graphs now clamp values >20% to the ceiling (20%)
instead of cropping them out.

Combined graphs:
 - avg_rtt_hops.png (Log Scale)
 - worst_rtt_hops.png (Log Scale)
 - stddev_hops.png (Log Scale)
 - packet_loss_hops.png (Linear Scale, Clamped at 20%)

Per-hop graphs folder included.
"""

import re
import os
import glob
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

# --- Configuration ---
TARGET_HOPS = [1, 2, 3, 4, 18]
EMA_SPAN = 10

# Professional color palette (Tab10)
TAB10 = plt.cm.tab10.colors
HOP_COLORS = {
    1: TAB10[0],
    2: TAB10[1],
    3: TAB10[2],
    4: TAB10[3],
    18: TAB10[4],
}

# --- Plotting Style Settings ---
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 11
plt.rcParams['figure.dpi'] = 150
plt.rcParams['lines.linewidth'] = 2

# Regex for hop rows
HOP_RE = re.compile(
    r"^\s*(\d+)\.\|\-\-\s+(\S+)\s+([0-9.]+|[?]{2,3})%\s+([0-9]+)\s+"
    r"([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)"
)

# Regex to extract timestamps
FILENAME_TS = re.compile(
    r".*?(\d{4})-(\d{2})-(\d{2})_(\d{2})-(\d{2})-(\d{2})"
)

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def extract_timestamp_from_filename(name):
    m = FILENAME_TS.search(name)
    if not m:
        return None
    y, mo, d, h, mi, s = map(int, m.groups())
    return datetime(y, mo, d, h, mi, s)

def parse_mtr(path):
    rows = []
    with open(path, "r", errors="ignore") as f:
        for line in f:
            m = HOP_RE.match(line)
            if not m:
                continue

            hop = int(m.group(1))
            host = m.group(2)
            loss_raw = m.group(3)
            loss = float(loss_raw) if loss_raw not in ("???", "??") else None
            
            avg = float(m.group(6))
            worst = float(m.group(8))
            stdev = float(m.group(9))

            rows.append((hop, host, loss, avg, worst, stdev))

    return pd.DataFrame(rows, columns=["hop", "host", "loss", "avg", "worst", "stdev"]).set_index("hop")

def setup_plot_style(ax, title, ylabel, log_scale=False, ylim=None):
    ax.set_title(title, fontweight='bold')
    ax.set_ylabel(ylabel)
    ax.set_xlabel("Date/Time")
    
    if ylim:
        ax.set_ylim(ylim)
    
    if log_scale:
        ax.set_yscale("log")
        ax.grid(True, which="both", linestyle="--", linewidth=0.5, alpha=0.5)
    else:
        ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.7)

    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())

def plot_combined(timestamps, data, metric_name, ylabel, output_name, ema_span=EMA_SPAN, log_scale=False, ylim=None):
    fig, ax = plt.subplots(figsize=(12, 6))

    for hop, values in data.items():
        s = pd.Series(values, index=timestamps, dtype="float")
        
        # CLAMPING LOGIC:
        # If a ceiling (ylim) is set, force values > ceiling to equal the ceiling.
        if ylim:
            # clip(upper=20) makes any 50% or 100% become exactly 20%
            s = s.clip(upper=ylim[1])

        # Trend Line
        ema = s.ewm(span=ema_span, adjust=False).mean()
        ax.plot(timestamps, ema, color=HOP_COLORS[hop], label=f"Hop {hop}", zorder=3, alpha=0.9)

        # Raw Dots
        ax.scatter(timestamps, s, s=10, color=HOP_COLORS[hop], alpha=0.25, edgecolors='none', zorder=2)

    setup_plot_style(ax, metric_name, ylabel, log_scale, ylim)
    
    ax.legend(loc='best', frameon=True, framealpha=0.9, fontsize='small')

    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(output_name, format='png')
    print(f"Saved Clean PNG: {output_name}")

def plot_single_hop(timestamps, values, hop, metric_name, ylabel, folder, ema_span=EMA_SPAN, log_scale=False, ylim=None):
    ensure_dir(folder)
    fig, ax = plt.subplots(figsize=(12, 5))

    s = pd.Series(values, index=timestamps, dtype="float")

    # CLAMPING LOGIC
    if ylim:
        s = s.clip(upper=ylim[1])

    ax.scatter(timestamps, s, s=12, color=HOP_COLORS[hop], alpha=0.3, edgecolors='none', zorder=2)
    ema = s.ewm(span=ema_span, adjust=False).mean()
    ax.plot(timestamps, ema, linewidth=2.5, color=HOP_COLORS[hop], zorder=3)

    setup_plot_style(ax, f"{metric_name} — Hop {hop}", ylabel, log_scale, ylim)
    
    fig.autofmt_xdate()
    fig.tight_layout()

    out_path = os.path.join(folder, f"hop_{hop}.png")
    fig.savefig(out_path, format='png')
    print(f"Saved PNG: {out_path}")

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(script_dir, "mtr_logs")

    files = sorted(glob.glob(os.path.join(log_dir, "*.txt")))
    if not files:
        print("No MTR logs found.")
        return

    timestamps = []
    avg_data = {hop: [] for hop in TARGET_HOPS}
    worst_data = {hop: [] for hop in TARGET_HOPS}
    std_data = {hop: [] for hop in TARGET_HOPS}
    loss_data = {hop: [] for hop in TARGET_HOPS}

    for path in files:
        name = os.path.basename(path)
        ts = extract_timestamp_from_filename(name)
        if ts is None: continue

        timestamps.append(ts)
        df = parse_mtr(path)

        for hop in TARGET_HOPS:
            if hop in df.index:
                avg_data[hop].append(df.loc[hop, "avg"])
                worst_data[hop].append(df.loc[hop, "worst"])
                std_data[hop].append(df.loc[hop, "stdev"])
                loss_val = df.loc[hop, "loss"]
                loss_data[hop].append(loss_val)
            else:
                for d in [avg_data, worst_data, std_data, loss_data]:
                    d[hop].append(None)

    # --- Combined Graphs ---
    plot_combined(timestamps, avg_data, "Average RTT", "ms", "avg_rtt_hops.png", log_scale=True)
    plot_combined(timestamps, worst_data, "Worst RTT", "ms", "worst_rtt_hops.png", log_scale=True)
    plot_combined(timestamps, std_data, "Jitter (StdDev)", "ms", "stddev_hops.png", log_scale=True)
    
    # Packet Loss: Clamped at 20% (Dots > 20% will sit on the 20% line)
    plot_combined(timestamps, loss_data, "Packet Loss", "%", "packet_loss_hops.png", log_scale=False, ylim=(0, 20))

    # --- Per-Hop Graphs ---
    folders = {"avg": "avg_rtt", "worst": "worst_rtt", "std": "stddev", "loss": "packet_loss"}
    for hop in TARGET_HOPS:
        plot_single_hop(timestamps, avg_data[hop], hop, "Average RTT", "ms", folders["avg"], log_scale=True)
        plot_single_hop(timestamps, worst_data[hop], hop, "Worst RTT", "ms", folders["worst"], log_scale=True)
        plot_single_hop(timestamps, std_data[hop], hop, "Jitter", "ms", folders["std"], log_scale=True)
        
        plot_single_hop(timestamps, loss_data[hop], hop, "Packet Loss", "%", folders["loss"], log_scale=False, ylim=(0, 20))

if __name__ == "__main__":
    main()