import os
import csv
import sys
import argparse
from collections import Counter
from pathlib import Path

# Try importing the library, handle error if missing
try:
    import pyexiv2
except ImportError:
    sys.exit("Error: pyexiv2 not found. Install it via 'pip install pyexiv2'")

SUPPORTED_EXTS = {'.jpg', '.jpeg', '.png', '.webp', '.tif', '.tiff'}

def get_tags_from_file(filepath):
    """Safely extracts XMP tags from a single file using pyexiv2."""
    try:
        # 1. Open metadata, read it
        metadata = pyexiv2.ImageMetadata(str(filepath))
        metadata.read()
        
        # 2. Check for the Xmp.dc.subject key
        tag_key = 'Xmp.dc.subject'
        if tag_key in metadata:
            # 3. Return the value (which is already a list)
            return metadata[tag_key].value
        else:
            return [] # No tags found
            
    except Exception:
        # Return empty if file is corrupted, unreadable, or not an image
        return [] 

def cmd_list_tags(args):
    """
    Logic for the 'list-tags' command.
    (This function is identical to the previous version)
    """
    target_dir = Path(args.path)
    if not target_dir.exists():
        sys.exit(f"Error: Directory '{target_dir}' not found.")

    print(f"Scanning {target_dir} for tags...")
    
    tag_counts = Counter()
    total_images = 0
    tagged_images = 0

    # 1. Recursive Scan
    for root, dirs, files in os.walk(target_dir):
        for file in files:
            if Path(file).suffix.lower() in SUPPORTED_EXTS:
                full_path = Path(root) / file
                total_images += 1
                
                tags = get_tags_from_file(full_path)
                if tags:
                    tagged_images += 1
                    tag_counts.update(tags)

    # 2. Sorting Logic
    sorted_tags = list(tag_counts.items())
    
    if args.sort == 'count':
        sorted_tags.sort(key=lambda x: (-x[1], x[0]))
    else:
        sorted_tags.sort(key=lambda x: x[0])

    # 3. Output Formatting
    output_lines = []
    
    if args.format == 'csv':
        output_lines.append("tag,count")
        for tag, count in sorted_tags:
            output_lines.append(f"{tag},{count}")
    
    else: # text or console format
        if not sorted_tags:
            output_lines.append("No tags found.")
        else:
            output_lines.append("All distinct tags:")
            output_lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            
            max_len = max((len(t[0]) for t in sorted_tags), default=10) + 5
            
            for tag, count in sorted_tags:
                if args.counts:
                    line = f"{tag:<{max_len}} ({count} images)"
                else:
                    line = tag
                output_lines.append(line)
                
            output_lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            output_lines.append(f"Total: {len(sorted_tags)} distinct tags")
            output_lines.append(f"Scanned: {total_images} images ({tagged_images} tagged)")

    # 4. Write Output
    content = "\n".join(output_lines)
    
    if args.output:
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"[✓] Output saved to: {args.output}")
        except IOError as e:
            print(f"Error writing file: {e}")
    else:
        print(content)

# --- CLI Argument Setup (main block) ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Image Tagger CLI")
    subparsers = parser.add_subparsers(dest='command', required=True)

    # List Tags Parser
    list_parser = subparsers.add_parser('list-tags', help='List all tags in collection')
    list_parser.add_argument('path', help='Folder to scan')
    list_parser.add_argument('--counts', action='store_true', help='Show image counts per tag')
    list_parser.add_argument('--sort', choices=['alpha', 'count'], default='alpha', help='Sort order')
    list_parser.add_argument('--output', help='Output file path (optional)')
    list_parser.add_argument('--format', choices=['txt', 'csv'], default='txt', help='Output format')
    
    # Run
    args = parser.parse_args()
    if args.command == 'list-tags':
        cmd_list_tags(args)