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

    # Create a complex grid: 4 rows, 2 columns.
    # Row 0: Download | Upload
    # Row 1: Latency | BufferBloat
    # Row 2: D/L+U/L | Latency+BufferBloat
    # Row 3: All-in-one (spans 2 cols)
    
    # Set a taller figure size to accommodate the extra rows
    fig = plt.figure(figsize=(18, 26))
    gs = fig.add_gridspec(4, 2, hspace=0.5, wspace=0.2) # Add some spacing
    fig.suptitle('Network Performance Over Time', fontsize=20, y=0.98)

    # --- Top Row (Originals) ---
    ax_dl = fig.add_subplot(gs[0, 0])
    ax_ul = fig.add_subplot(gs[0, 1])
    
    # --- Second Row (Originals) ---
    ax_lat = fig.add_subplot(gs[1, 0])
    ax_bb = fig.add_subplot(gs[1, 1])
    
    # --- Third Row (New Overlays) ---
    ax_speeds = fig.add_subplot(gs[2, 0])
    ax_latency = fig.add_subplot(gs[2, 1])
    
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

    # --- Plot 3: Latency (Original) ---
    ax_lat.plot(timestamps, latencies, marker='.', linestyle='-', markersize=8, color='red', label='Latency')
    ax_lat.set_title('Latency (Ping)', fontsize=14)
    ax_lat.set_ylabel('ms (milliseconds) - Log Scale')
    ax_lat.set_yscale('log') # Use log scale for large spikes
    ax_lat.grid(True, linestyle='--', alpha=0.6)
    ax_lat.legend(loc='upper left')

    # --- Plot 4: BufferBloat (Original) ---
    ax_bb.plot(timestamps, bufferbloats, marker='.', linestyle='-', markersize=8, color='purple', label='BufferBloat')
    ax_bb.set_title('BufferBloat', fontsize=14)
    ax_bb.set_ylabel('ms (milliseconds) - Log Scale')
    ax_bb.set_yscale('log') # Use log scale for large spikes
    ax_bb.grid(True, linestyle='--', alpha=0.6)
    ax_bb.legend(loc='upper left')

    # --- Plot 5: Download & Upload Overlaid ---
    ax_speeds.plot(timestamps, downloads, marker='.', linestyle='-', markersize=8, color='deepskyblue', label='Download')
    ax_speeds.plot(timestamps, uploads, marker='.', linestyle='-', markersize=8, color='green', label='Upload')
    ax_speeds.set_title('Download & Upload Speeds', fontsize=14)
    ax_speeds.set_ylabel('Mbps')
    ax_speeds.grid(True, linestyle='--', alpha=0.6)
    ax_speeds.legend(loc='upper left')

    # --- Plot 6: Latency & BufferBloat Overlaid ---
    ax_latency.plot(timestamps, latencies, marker='.', linestyle='-', markersize=8, color='red', label='Latency')
    ax_latency.plot(timestamps, bufferbloats, marker='.', linestyle='-', markersize=8, color='purple', label='BufferBloat')
    ax_latency.set_title('Latency & BufferBloat', fontsize=14)
    ax_latency.set_ylabel('ms (milliseconds) - Log Scale')
    ax_latency.set_yscale('log') # Use log scale for large spikes
    ax_latency.grid(True, linestyle='--', alpha=0.6)
    ax_latency.legend(loc='upper left')

    # --- Plot 7: Everything Overlaid (Larger) ---
    # This plot needs a secondary y-axis due to scale differences
    ax_all_twin = ax_all.twinx() # Create a second y-axis

    # Plot speeds on the left axis
    p1, = ax_all.plot(timestamps, downloads, marker='.', linestyle='-', markersize=8, color='deepskyblue', label='Download (Mbps)')
    p2, = ax_all.plot(timestamps, uploads, marker='.', linestyle='-', markersize=8, color='green', label='Upload (Mbps)')
    ax_all.set_ylabel('Mbps (Speeds)', color='deepskyblue')
    ax_all.tick_params(axis='y', labelcolor='deepskyblue')

    # Plot latencies on the right axis
    p3, = ax_all_twin.plot(timestamps, latencies, marker='.', linestyle='--', markersize=8, color='red', label='Latency (ms)')
    p4, = ax_all_twin.plot(timestamps, bufferbloats, marker='.', linestyle='--', markersize=8, color='purple', label='BufferBloat (ms)')
    ax_all_twin.set_ylabel('ms (Latency) - Log Scale', color='red')
    ax_all_twin.tick_params(axis='y', labelcolor='red')
    ax_all_twin.set_yscale('log') # Use log scale for large spikes

    ax_all.set_title('All Metrics Overlaid', fontsize=16)
    ax_all.grid(True, linestyle='--', alpha=0.6)
    
    # Add a combined legend for the "everything" plot
    lines = [p1, p2, p3, p4]
    ax_all.legend(lines, [l.get_label() for l in lines], loc='upper left')


    # Format all X-axes ---
    all_axes = [ax_dl, ax_ul, ax_lat, ax_bb, ax_speeds, ax_latency, ax_all]
    
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