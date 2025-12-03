import os
import glob
import json

def concat_json_files(output_filename="concatenated_data.json"):
    # Get the current working directory
    current_dir = os.getcwd()
    
    # Find all JSON files in the current directory
    # glob.glob('*.json') returns a list of all files ending in .json
    json_files = glob.glob('*.json')
    
    # Sort files to ensure consistent order (optional, but helpful)
    json_files.sort()
    
    if not json_files:
        print("No JSON files found in the current directory.")
        return

    print(f"Found {len(json_files)} JSON files. Starting concatenation...")

    # Dictionary to hold all data: { "filename.json": {data} }
    all_data = {}

    for filename in json_files:
        # Skip the output file itself if it exists in the list
        if filename == output_filename:
            continue

        try:
            with open(filename, 'r', encoding='utf-8') as infile:
                # Load the JSON content from the file
                file_content = json.load(infile)
                
                # Add to the master dictionary with the filename as the key
                all_data[filename] = file_content
                    
            print(f"Processed: {filename}")
        except json.JSONDecodeError:
            print(f"Error: {filename} is not a valid JSON file. Skipping.")
        except Exception as e:
            print(f"Error reading {filename}: {e}")

    # Write the valid JSON object to the output file
    try:
        with open(output_filename, 'w', encoding='utf-8') as outfile:
            json.dump(all_data, outfile, indent=4)
    except Exception as e:
        print(f"Error writing output file: {e}")

    print(f"\nSuccess! All data concatenated into: {os.path.join(current_dir, output_filename)}")

if __name__ == "__main__":
    concat_json_files()