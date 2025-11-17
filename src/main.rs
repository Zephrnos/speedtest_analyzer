use serde::Deserialize;
use std::fs;

// Struct to hold only the data we care about from the JSON.
// #[serde(rename_all = "camelCase")] handles the JSON's field_names
#[derive(Debug, Deserialize, Clone)]
#[serde(rename_all = "camelCase")]
struct SpeedTestResult {
    download_speed: f64,
    upload_speed: f64,
    latency: f64,
    buffer_bloat: f64,
}

// Struct to associate the parsed result with its original filename
#[derive(Debug, Clone)]
struct TestEntry {
    filename: String,
    result: SpeedTestResult,
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut all_results: Vec<TestEntry> = Vec::new();

    // Read all entries in the current directory (".")
    for entry in fs::read_dir(".")? {
        let entry = entry?;
        let path = entry.path();

        // We only care about files that end in .json
        if path.is_file() && path.extension().map_or(false, |s| s == "json") {
            let filename = path.file_name().unwrap_or_default().to_string_lossy().to_string();
            
            let content = match fs::read_to_string(&path) {
                Ok(c) => c,
                Err(e) => {
                    eprintln!("!> Failed to read {}: {}. Skipping.", filename, e);
                    continue;
                }
            };

            // Handle empty files, which are not valid JSON
            if content.trim().is_empty() {
                eprintln!("!> Skipping empty file: {}", filename);
                continue;
            }

            // Try to parse the file's content
            match serde_json::from_str::<SpeedTestResult>(&content) {
                Ok(result) => {
                    all_results.push(TestEntry { filename, result });
                },
                Err(e) => {
                    eprintln!("!> Failed to parse {}: {}. Skipping.", filename, e);
                }
            }
        }
    }

    if all_results.is_empty() {
        println!("No valid speedtest JSON files found in this directory.");
        return Ok(());
    }

    println!("--- Found and analyzed {} valid reports ---", all_results.len());

    // --- 1. Worst Download (Lowest is worst) ---
    let mut by_download = all_results.clone();
    // Sort by f64, using partial_cmp for floats. Lowest first.
    by_download.sort_by(|a, b| a.result.download_speed.partial_cmp(&b.result.download_speed).unwrap_or(std::cmp::Ordering::Equal));
    
    println!("\n### 3 Worst Download Speeds (Lowest) ###");
    for entry in by_download.iter().take(3) {
        println!("  - {}: {:.2} Mbps", entry.filename, entry.result.download_speed);
    }

    // --- 2. Worst Upload (Lowest is worst) ---
    let mut by_upload = all_results.clone();
    by_upload.sort_by(|a, b| a.result.upload_speed.partial_cmp(&b.result.upload_speed).unwrap_or(std::cmp::Ordering::Equal));
    
    println!("\n### 3 Worst Upload Speeds (Lowest) ###");
    for entry in by_upload.iter().take(3) {
        println!("  - {}: {:.2} Mbps", entry.filename, entry.result.upload_speed);
    }

    // --- 3. Worst Latency (Highest is worst) ---
    let mut by_latency = all_results.clone();
    // Sort in REVERSE. Highest first. Note `b.cmp(a)`
    by_latency.sort_by(|a, b| b.result.latency.partial_cmp(&a.result.latency).unwrap_or(std::cmp::Ordering::Equal));
    
    println!("\n### 3 Worst Latency (Highest) ###");
    for entry in by_latency.iter().take(3) {
        println!("  - {}: {:.2} ms", entry.filename, entry.result.latency);
    }

    // --- 4. Worst BufferBloat (Highest is worst) ---
    let mut by_bufferbloat = all_results.clone();
    // Sort in REVERSE. Highest first.
    by_bufferbloat.sort_by(|a, b| b.result.buffer_bloat.partial_cmp(&a.result.buffer_bloat).unwrap_or(std::cmp::Ordering::Equal));
    
    println!("\n### 3 Worst BufferBloat (Highest) ###");
    for entry in by_bufferbloat.iter().take(3) {
        println!("  - {}: {:.2} ms", entry.filename, entry.result.buffer_bloat);
    }

    Ok(())
}