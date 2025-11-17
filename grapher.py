#!/usr/bin/env python3

"""
Generates time-series graphs from a directory of speedtest.net JSON reports.

Reports are expected to be in the format 'speedtest-YYYY-MM-DD_HH-MM-SS.json'.
This script will parse all such files in its current directory, sort them
by time, and generate a 2x2 plot of the key metrics.

Empty or malformed JSON files will be skipped and noted in the console.
"""

import glob
import json
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np # Import numpy for break lines

def parse_filename_timestamp(filename):
    """Extracts the datetime object from the speedtest filename."""
    # Filename format is 'speedtest-YYYY-MM-DD_HH-MM-SS.json'
    # We extract the timestamp part: 'YYYY-MM-DD_HH-MM-SS'
    try:
        timestamp_str = filename[10:-5] # Assumes './speedtest-' prefix if run with glob
        if timestamp_str.startswith('speedtest-'): # Handle case where glob returns full name
             timestamp_str = filename[10:-5]
        
        # Adjust for local paths like 'speedtest-...' vs 'path/to/speedtest-...'
        # Find the start of the date part
        date_start_index = timestamp_str.find('20') 
        if date_start_index != -1:
            timestamp_str = timestamp_str[date_start_index:]
            
        return datetime.strptime(timestamp_str, '%Y-%m-%d_%H-%M-%S')
    except (ValueError, IndexError) as e:
        print(f"[Warning] Could not parse timestamp from filename: {filename}. Error: {e}")
        return None

def load_speedtest_data():
    """Loads all speedtest.json files from the current directory."""
    all_data = []
    # Find all files matching the pattern
    json_files = sorted(glob.glob('speedtest-*.json'))
    
    if not json_files:
        print("[Error] No 'speedtest-*.json' files found in this directory.")
        return []

    print(f"--- Found {len(json_files)} report files ---")

    for filename in json_files:
        # 1. Parse timestamp from filename
        timestamp = parse_filename_timestamp(filename)
        if not timestamp:
            continue

        # 2. Parse data from JSON file content
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                
                # Ensure all keys are present
                download = data['downloadSpeed']
                upload = data['uploadSpeed']
                latency = data['latency']
                bufferbloat = data['bufferBloat']
                
                all_data.append((
                    timestamp,
                    download,
                    upload,
                    latency,
                    bufferbloat
                ))

        except json.JSONDecodeError:
            print(f"!> Treating empty file as outage: {filename}")
            # Add outage data: 0 speed, 1000ms latency/buffer
            all_data.append((timestamp, 0, 0, 1000, 1000)) 
        except KeyError as e:
            print(f"!> Skipping file with missing data key {e}: {filename}")
        except Exception as e:
            print(f"!> An unexpected error occurred with {filename}: {e}")

    # 3. Sort all data by timestamp (the first element of our tuple)
    all_data.sort()
    
    print(f"--- Successfully parsed {len(all_data)} valid reports ---")
    return all_data

def add_break_lines(ax_top, ax_bottom):
    """Draws the diagonal 'break' lines on a broken y-axis."""
    # This is a bit of magic to draw the lines
    d = .015 # how big to make the diagonal lines
    kwargs = dict(transform=ax_top.transAxes, color='k', clip_on=False)
    ax_top.plot((-d,+d), (-d,+d), **kwargs)        # top-left diagonal
    ax_top.plot((1-d,1+d), (-d,+d), **kwargs)    # top-right diagonal

    kwargs.update(transform=ax_bottom.transAxes)  # switch to the bottom axes
    ax_bottom.plot((-d,+d), (1-d,1+d), **kwargs)  # bottom-left diagonal
    ax_bottom.plot((1-d,1+d), (1-d,1+d), **kwargs) # bottom-right diagonal

def create_plots(data):
    """Generates and saves a 2x2 plot of the speedtest data."""
    if not data:
        print("[Error] No valid data to plot.")
        return

    # "Unzip" the sorted data into separate lists for plotting
    timestamps = [d[0] for d in data]
    downloads = [d[1] for d in data]
    uploads = [d[2] for d in data]
    latencies = [d[3] for d in data]
    bufferbloats = [d[4] for d in data]

    # Find max "normal" values to set y-limits, ignoring outages (1000ms)
    # We find the max value under 500, or default to 50 if all are outages
    max_normal_latency = max([l for l in latencies if l < 500] or [50])
    max_normal_bufferbloat = max([b for b in bufferbloats if b < 500] or [50])
    
    # Set a reasonable top limit, e.g., 20% above the max normal, or a min of 50
    lat_ylim = max(max_normal_latency * 1.2, 50)
    bb_ylim = max(max_normal_bufferbloat * 1.2, 50)
    
    # Combine for the shared "latency" plot and "all" plot
    max_combined_lat_bb = max(lat_ylim, bb_ylim)

    # Create a complex grid: 4 rows, 2 columns.
    # Row 0: Download | Upload
    # Row 1: Latency | BufferBloat
    # Row 2: D/L+U/L | Latency+BufferBloat
    # Row 3: All-in-one (spans 2 cols)
    
    # Set a taller figure size to accommodate the extra rows
    # Increased height even more for the axis breaks
    fig = plt.figure(figsize=(18, 28)) 
    # Add more horizontal space for the axis breaks
    gs = fig.add_gridspec(4, 2, hspace=0.7, wspace=0.3) 
    fig.suptitle('Network Performance Over Time', fontsize=20, y=0.98)

    # --- Top Row (Originals) ---
    ax_dl = fig.add_subplot(gs[0, 0])
    ax_ul = fig.add_subplot(gs[0, 1])
    
    # --- Second Row (Originals - Now Broken Axis) ---
    # We create a sub-grid for the latency plot
    gs_lat = gs[1, 0].subgridspec(2, 1, hspace=0.1)
    ax_lat_top = fig.add_subplot(gs_lat[0, 0])
    ax_lat_bottom = fig.add_subplot(gs_lat[1, 0])
    
    # And a sub-grid for the bufferbloat plot
    gs_bb = gs[1, 1].subgridspec(2, 1, hspace=0.1)
    ax_bb_top = fig.add_subplot(gs_bb[0, 0])
    ax_bb_bottom = fig.add_subplot(gs_bb[1, 0])
    
    # --- Third Row (New Overlays - Now Broken Axis) ---
    ax_speeds = fig.add_subplot(gs[2, 0])
    
    # Sub-grid for the overlaid latency/bb plot
    gs_latency = gs[2, 1].subgridspec(2, 1, hspace=0.1)
    ax_latency_top = fig.add_subplot(gs_latency[0, 0])
    ax_latency_bottom = fig.add_subplot(gs_latency[1, 0])
    
    # --- Fourth Row (New "Everything" Plot) ---
    ax_all = fig.add_subplot(gs[3, :]) # Spans both columns

    # --- Plot 1: Download Speed (Original) ---
    ax_dl.plot(timestamps, downloads, marker='.', linestyle='-', markersize=8, color='deepskyblue', label='Download')
    ax_dl.set_title('Download Speed', fontsize=14)
    ax_dl.set_ylabel('Mbps')
    ax_dl.grid(True, linestyle='--', alpha=0.6)
    ax_dl.legend(loc='upper left')
    
    # --- Plot 2: Upload Speed (Original) ---
    ax_ul.plot(timestamps, uploads, marker='.', linestyle='-', markersize=8, color='green', label='Upload')
    ax_ul.set_title('Upload Speed', fontsize=14)
    ax_ul.set_ylabel('Mbps')
    ax_ul.grid(True, linestyle='--', alpha=0.6)
    ax_ul.legend(loc='upper left')

    # --- Plot 3: Latency (Original - BROKEN) ---
    for ax in [ax_lat_top, ax_lat_bottom]:
        ax.plot(timestamps, latencies, marker='.', linestyle='-', markersize=8, color='red', label='Latency')
        ax.grid(True, linestyle='--', alpha=0.6)

    ax_lat_top.set_ylim(bottom=950, top=1050) # Outage view
    ax_lat_bottom.set_ylim(bottom=0, top=lat_ylim) # Normal view

    ax_lat_top.set_title('Latency (Ping)', fontsize=14)
    ax_lat_bottom.set_ylabel('ms (milliseconds)')
    ax_lat_top.legend(loc='upper left')
    
    # Hide spines and labels
    ax_lat_top.spines['bottom'].set_visible(False)
    ax_lat_bottom.spines['top'].set_visible(False)
    ax_lat_top.xaxis.set_major_formatter(plt.NullFormatter()) # No x-labels on top
    
    # Add the break lines
    add_break_lines(ax_lat_top, ax_lat_bottom)

    # --- Plot 4: BufferBloat (Original - BROKEN) ---
    for ax in [ax_bb_top, ax_bb_bottom]:
        ax.plot(timestamps, bufferbloats, marker='.', linestyle='-', markersize=8, color='purple', label='BufferBloat')
        ax.grid(True, linestyle='--', alpha=0.6)

    ax_bb_top.set_ylim(bottom=950, top=1050) # Outage view
    ax_bb_bottom.set_ylim(bottom=0, top=bb_ylim) # Normal view

    ax_bb_top.set_title('BufferBloat', fontsize=14)
    ax_bb_bottom.set_ylabel('ms (milliseconds)')
    ax_bb_top.legend(loc='upper left')

    # Hide spines and labels
    ax_bb_top.spines['bottom'].set_visible(False)
    ax_bb_bottom.spines['top'].set_visible(False)
    ax_bb_top.xaxis.set_major_formatter(plt.NullFormatter()) # No x-labels on top

    # Add the break lines
    add_break_lines(ax_bb_top, ax_bb_bottom)

    # --- Plot 5: Download & Upload Overlaid ---
    ax_speeds.plot(timestamps, downloads, marker='.', linestyle='-', markersize=8, color='deepskyblue', label='Download')
    ax_speeds.plot(timestamps, uploads, marker='.', linestyle='-', markersize=8, color='green', label='Upload')
    ax_speeds.set_title('Download & Upload Speeds', fontsize=14)
    ax_speeds.set_ylabel('Mbps')
    ax_speeds.grid(True, linestyle='--', alpha=0.6)
    ax_speeds.legend(loc='upper left')

    # --- Plot 6: Latency & BufferBloat Overlaid (BROKEN) ---
    for ax in [ax_latency_top, ax_latency_bottom]:
        ax.plot(timestamps, latencies, marker='.', linestyle='-', markersize=8, color='red', label='Latency')
        ax.plot(timestamps, bufferbloats, marker='.', linestyle='-', markersize=8, color='purple', label='BufferBloat')
        ax.grid(True, linestyle='--', alpha=0.6)
    
    ax_latency_top.set_ylim(bottom=950, top=1050) # Outage view
    ax_latency_bottom.set_ylim(bottom=0, top=max_combined_lat_bb) # Normal view
    
    ax_latency_top.set_title('Latency & BufferBloat', fontsize=14)
    ax_latency_bottom.set_ylabel('ms (milliseconds)')
    ax_latency_top.legend(loc='upper left')

    # Hide spines and labels
    ax_latency_top.spines['bottom'].set_visible(False)
    ax_latency_bottom.spines['top'].set_visible(False)
    ax_latency_top.xaxis.set_major_formatter(plt.NullFormatter()) # No x-labels on top

    # Add the break lines
    add_break_lines(ax_latency_top, ax_latency_bottom)


    # --- Plot 7: Everything Overlaid (Larger) ---
    # This plot is NOT broken, as it's too complex. Uses text annotation.
    ax_all_twin.set_ylim(bottom=0, top=max_combined_lat_bb) # Set linear ylim

    ax_all.set_title('All Metrics Overlaid', fontsize=16)
    ax_all.grid(True, linestyle='--', alpha=0.6)
    
    # Add a combined legend for the "everything" plot
    lines = [p1, p2, p3, p4]
    ax_all.legend(lines, [l.get_label() for l in lines], loc='upper left')


    # --- Add Outage Annotations (FOR PLOT 7 ONLY) ---
    # This loop adds "OUTAGE" text to the charts where data is 1000
    for i, ts in enumerate(timestamps):
        # Check for latency outage
        if latencies[i] == 1000:
            ax_all_twin.text(ts, max_combined_lat_bb * 0.9, 'OUTAGE', ha='center', color='red', fontsize=10, weight='bold', bbox=dict(facecolor='white', alpha=0.8, pad=0.1))
        
        # Check for bufferbloat outage
        if bufferbloats[i] == 1000:
            # Avoid double-labeling
            if latencies[i] != 1000: 
                ax_all_twin.text(ts, max_combined_lat_bb * 0.9, 'OUTAGE', ha='center', color='purple', fontsize=10, weight='bold', bbox=dict(facecolor='white', alpha=0.8, pad=0.1))


    # Format all X-axes ---
    # Note: We now target the 'bottom' axes for the broken charts
    all_axes = [ax_dl, ax_ul, ax_lat_bottom, ax_bb_bottom, ax_speeds, ax_latency_bottom, ax_all]
    
    date_format = mdates.DateFormatter('%m-%d %H:%M')
    for ax in all_axes:
        ax.xaxis.set_major_formatter(date_format)
        ax.set_xlabel('Timestamp')
        # Manually set rotation for tick labels on all axes
        plt.setp(ax.get_xticklabels(), rotation=30, ha='right')
    
    # Auto-rotate the x-axis labels for readability
    # fig.autofmt_xdate() # Remove this, as we are setting rotation manually

    # Adjust layout
    plt.tight_layout(rect=[0, 0.03, 1, 0.95]) # Leave space for the main title

    # Save the final graph to a file
    output_filename = 'speedtest_analysis.png'
    plt.savefig(output_filename)
    
    print(f"\n[Success] Graph saved as '{output_filename}'")
    
    # Optionally, display the plot in a window
    # plt.show() 

def main():
    data = load_speedtest_data()
    create_plots(data)

if __name__ == "__main__":
    main()