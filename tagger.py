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

# --- METADATA HELPER FUNCTIONS (READ & WRITE) ---

def get_tags_from_file(filepath):
    """Safely extracts XMP tags from a single file using pyexiv2."""
    try:
        metadata = pyexiv2.ImageMetadata(str(filepath))
        metadata.read()
        
        tag_key = 'Xmp.dc.subject'
        if tag_key in metadata:
            return metadata[tag_key].value or []
        else:
            return []
    except Exception:
        return [] 

def set_tags_on_file(filepath, tags_to_add):
    """
    Adds a list of tags to a file, merging with existing tags.
    Returns (success_bool, total_tags_list)
    """
    try:
        metadata = pyexiv2.ImageMetadata(str(filepath))
        metadata.read()
        
        # Get existing tags
        tag_key = 'Xmp.dc.subject'
        existing_tags = metadata.get(tag_key, {}).get('value', [])
        
        # Merge tags, ensuring no duplicates
        updated_tags = sorted(list(set(existing_tags) | set(tags_to_add)))
        
        # Write back to metadata object
        metadata[tag_key] = updated_tags
        
        # Save changes to the file
        metadata.write()
        
        return (True, updated_tags)
        
    except Exception as e:
        print(f"  [!] Error writing to {filepath.name}: {e}", file=sys.stderr)
        return (False, existing_tags)

# --- COMMAND IMPLEMENTATION: AUTO-TAG ---

def cmd_auto_tag(args):
    """Logic for the 'auto-tag' command."""
    root_dir = Path(args.path).resolve()
    if not root_dir.exists():
        sys.exit(f"Error: Directory '{root_dir}' not found.")

    if args.dry_run:
        print(f"[AUTO-TAG] DRY-RUN: Scanning {root_dir} recursively...")
        print("No files will be modified.")
    else:
        print(f"[AUTO-TAG] Scanning {root_dir} recursively...")

    total_images = 0
    processed_images = 0
    all_tag_chains = set()
    total_tags_added = 0

    image_files = []
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if Path(file).suffix.lower() in SUPPORTED_EXTS:
                image_files.append(Path(root) / file)
                total_images += 1
    
    print(f"Found {total_images} images.")
    if total_images == 0:
        return

    print("\nProcessing:")

    for img_path in image_files:
        # Get path relative to the root dir
        # e.g., Wallpapers/Nature/peak.jpg
        try:
            relative_path = img_path.relative_to(root_dir)
        except ValueError:
            print(f"  [!] Skipping {img_path} (not in root)", file=sys.stderr)
            continue
            
        # Get parent directory parts
        # e.g., ['Wallpapers', 'Nature']
        parts = list(relative_path.parent.parts)
        
        if not parts:
            continue # Skip images in the root folder

        # Apply max-depth limit
        if args.max_depth and len(parts) > args.max_depth:
            parts = parts[:args.max_depth]
            
        if not parts:
            continue # Skip if max-depth is 0 or invalid

        # Build tag chains
        # e.g., ['wallpapers', 'wallpapers/nature']
        generated_tags = []
        current_chain = ""
        for part in parts:
            # Note: Using lowercase as shown in the spec example
            current_chain_part = part.lower() 
            current_chain = f"{current_chain}/{current_chain_part}" if current_chain else current_chain_part
            generated_tags.append(current_chain)
        
        all_tag_chains.add(tuple(parts))
        processed_images += 1
        
        # Display progress
        print(f"  {img_path.relative_to(root_dir)}")
        
        if args.dry_run:
            print(f"    Tags (Dry Run): {generated_tags}")
        else:
            success, final_tags = set_tags_on_file(img_path, generated_tags)
            if success:
                print(f"    Tags: {final_tags}")
                total_tags_added += len(generated_tags)
            
    # Print Summary
    avg_tags = (total_tags_added / processed_images) if processed_images > 0 else 0
    
    print("\nSummary:")
    print(f"  • Images processed: {processed_images}")
    print(f"  • Unique tag chains: {len(all_tag_chains)}")
    if not args.dry_run:
        print(f"  • Total tags added: {total_tags_added}")
        print(f"  • Average tags per image: {avg_tags:.1f}")
    if args.dry_run:
        print("\nDRY-RUN complete. No files were changed.")


# --- COMMAND IMPLEMENTATION: LIST-TAGS ---

def cmd_list_tags(args):
    """Logic for the 'list-tags' command."""
    target_dir = Path(args.path)
    if not target_dir.exists():
        sys.exit(f"Error: Directory '{target_dir}' not found.")

    print(f"Scanning {target_dir} for tags...")
    
    tag_counts = Counter()
    total_images = 0
    tagged_images = 0

    for root, dirs, files in os.walk(target_dir):
        for file in files:
            if Path(file).suffix.lower() in SUPPORTED_EXTS:
                full_path = Path(root) / file
                total_images += 1
                
                tags = get_tags_from_file(full_path)
                if tags:
                    tagged_images += 1
                    tag_counts.update(tags)

    sorted_tags = list(tag_counts.items())
    
    if args.sort == 'count':
        sorted_tags.sort(key=lambda x: (-x[1], x[0]))
    else:
        sorted_tags.sort(key=lambda x: x[0])

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

# --- CLI ARGUMENT SETUP (MAIN BLOCK) ---

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Image Tagger CLI")
    subparsers = parser.add_subparsers(dest='command', required=True)

    # --- List Tags Parser ---
    list_parser = subparsers.add_parser('list-tags', help='List all tags in collection')
    list_parser.add_argument('path', help='Folder to scan')
    list_parser.add_argument('--counts', action='store_true', help='Show image counts per tag')
    list_parser.add_argument('--sort', choices=['alpha', 'count'], default='alpha', help='Sort order')
    list_parser.add_argument('--output', help='Output file path (optional)')
    list_parser.add_argument('--format', choices=['txt', 'csv'], default='txt', help='Output format')
    list_parser.set_defaults(func=cmd_list_tags)

    # --- Auto-Tag Parser ---
    auto_tag_parser = subparsers.add_parser('auto-tag', help='Auto-tag images from folder structure')
    auto_tag_parser.add_argument('path', help='Root folder to scan')
    auto_tag_parser.add_argument('--dry-run', action='store_true', help='Preview changes without writing')
    auto_tag_parser.add_argument('--max-depth', type=int, help='Max folder depth to create tags from')
    auto_tag_parser.set_defaults(func=cmd_auto_tag)
    
    # --- Run ---
    args = parser.parse_args()
    # Call the function associated with the chosen subcommand
    args.func(args)