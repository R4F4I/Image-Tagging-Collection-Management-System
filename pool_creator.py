import argparse
import csv
import sys
from pathlib import Path
import shutil


def read_csv_data(filepath):
    """Reads data from a CSV file and returns a list of dictionaries."""
    if not filepath.exists():
        sys.exit(f"Error: Input CSV file not found at '{filepath}'")
    
    try:
        with open(filepath, mode='r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            # Sanitize field names to prevent issues with BOM or whitespace
            reader.fieldnames = [name.strip().lower() for name in reader.fieldnames]
            
            # Check for required columns
            if 'filepath' not in reader.fieldnames or 'tags' not in reader.fieldnames:
                sys.exit(f"Error: CSV '{filepath}' must have 'filepath' and 'tags' columns.")

            return list(reader)
    except Exception as e:
        sys.exit(f"Error reading CSV file '{filepath}': {e}")


def main():
    """Main function to create image pools."""
    parser = argparse.ArgumentParser(
        description="Organize images by moving them into subdirectories based on tags.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        '--data-csv',
        required=True,
        help="Path to the main CSV file with image filepaths and tags (e.g., 'shape_tags.csv')."
    )
    parser.add_argument(
        '--pool-csv',
        required=True,
        help="Path to the CSV file defining the pools.\nMust contain 'pool_name' and 'required_tags' columns."
    )
    args = parser.parse_args()

    data_csv_path = Path(args.data_csv)
    pool_csv_path = Path(args.pool_csv)

    # --- 1. Read Input Data ---
    print(f"Reading image data from '{data_csv_path}'...")
    image_data = read_csv_data(data_csv_path)
    print(f"Found {len(image_data)} image records.")

    print(f"\nReading pool definitions from '{pool_csv_path}'...")
    # Custom reading for pool definitions
    if not pool_csv_path.exists():
        sys.exit(f"Error: Pool definition CSV not found at '{pool_csv_path}'")
    
    try:
        with open(pool_csv_path, mode='r', encoding='utf-8') as infile:
            # Read the first line to determine the header format
            first_line = infile.readline()
            if not first_line:
                sys.exit(f"Error: Pool CSV file '{pool_csv_path}' is empty.")

            # Determine fieldnames, filtering out empty ones from trailing commas
            fieldnames = [name.strip().lower() for name in first_line.strip().split(',') if name.strip()]

            # IMPORTANT: Rewind the file to read from the beginning
            infile.seek(0)

            pool_definitions = []
            # If it's a simple, single-column list of tags
            if len(fieldnames) == 1:
                print("Detected simple one-column format for pool definitions.")
                reader = csv.reader(infile)
                # Each row (including the header) is a pool definition
                pool_definitions = [{'pool_name': row[0].strip(), 'required_tags': row[0].strip()} for row in reader if row and row[0].strip()]
            # If it's the standard format
            elif 'pool_name' in fieldnames and 'required_tags' in fieldnames:
                print("Detected standard 'pool_name', 'required_tags' format.")
                dict_reader = csv.DictReader(infile)
                pool_definitions = list(dict_reader)
            else:
                sys.exit(f"Error: Pool CSV '{pool_csv_path}' has an invalid header. It must have either a single column of tags, or 'pool_name' and 'required_tags' columns.")
    except Exception as e:
        sys.exit(f"Error reading pool definition file: {e}")

    print(f"Found {len(pool_definitions)} pool definitions.")

    # --- 2. Process Pools ---
    print("\nPlanning file organization...")
    
    moves_to_make = []
    # This dictionary will hold the results for each pool's report
    pool_reports = {pool.get('pool_name'): [] for pool in pool_definitions}

    # --- PASS 1: Decide where each file should go without moving anything ---
    for record in image_data:
        image_path = Path(record['filepath'])
        if image_path.suffix.lower() not in {'.jpg', '.jpeg', '.png', '.webp', '.tif', '.tiff'}:
            continue
        
        image_tags = {tag.strip() for tag in record.get('tags', '').split(',') if tag.strip()}

        for pool in pool_definitions:
            pool_name = pool.get('pool_name', '').strip()
            required_tags_str = pool.get('required_tags', '').strip()
            if not pool_name or not required_tags_str:
                continue
            
            required_tags = {tag.strip() for tag in required_tags_str.split(',') if tag.strip()}

            if required_tags.issubset(image_tags):
                # The source path is relative to the CSV's location
                source_file = data_csv_path.parent / image_path
                dest_dir = source_file.parent / pool_name
                moves_to_make.append({'source': source_file, 'dest': dest_dir, 'pool_name': pool_name, 'record': record})
                # Once a home is found, stop checking other pools for this image
                break
    
    print(f"Found {len(moves_to_make)} files to organize.")
    print("\nExecuting file moves...")
    
    # --- PASS 2: Execute all the planned moves and collect report data ---
    for move in moves_to_make:
        source_path = move['source']
        dest_dir = move['dest']
        pool_name = move['pool_name']
        
        if not source_path.exists():
            print(f"  [!] Skipping '{source_path.name}', it was already moved or does not exist.")
            continue
        
        dest_dir.mkdir(parents=True, exist_ok=True)
        try:
            new_path = shutil.move(source_path, dest_dir)
            # Update the record for the report with the new relative path
            relative_new_path = Path(new_path).relative_to(data_csv_path.parent)
            move['record']['filepath'] = str(relative_new_path).replace('\\', '/')
            pool_reports[pool_name].append(move['record'])
            print(f"  [✓] Moved '{source_path.name}' to '{dest_dir.name}/'")
        except Exception as e:
            print(f"  [!] Could not move '{source_path.name}': {e}")

    # --- 3. Write all reports at the end ---
    print("\nWriting reports...")
    for pool_name, report_data in pool_reports.items():
        if report_data:
            # The report is written inside the new pool directory
            report_dir = data_csv_path.parent / report_data[0]['filepath']
            report_path = report_dir.parent / f'_report_{pool_name}.csv'
            
            try:
                with open(report_path, 'w', newline='', encoding='utf-8') as report_file:
                    writer = csv.DictWriter(report_file, fieldnames=['filepath', 'tags'])
                    writer.writeheader()
                    writer.writerows(report_data)
                print(f"  [✓] Wrote report for '{pool_name}' with {len(report_data)} items.")
            except IOError as e:
                print(f"  [!] Could not write report for '{pool_name}': {e}")

if __name__ == "__main__":
    main()