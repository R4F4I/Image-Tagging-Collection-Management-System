import os
import csv
import sys
import argparse
import re
from collections import Counter
from pathlib import Path
from glob import glob

# Try importing the library, handle error if missing
try:
    import pyexiv2
except ImportError:
    sys.exit("Error: pyexiv2 not found. Install it via 'pip install pyexiv2'")

SUPPORTED_EXTS = {'.jpg', '.jpeg', '.png', '.webp', '.tif', '.tiff'}

# --- CORE "ENGINE" FUNCTIONS (READ & WRITE) ---

def get_tags_from_file(filepath):
    """Safely extracts XMP tags from a single file using pyexiv2."""
    try:
        img = pyexiv2.Image(str(filepath))
        xmp_data = img.read_xmp()
        img.close()
        return xmp_data.get('Xmp.dc.subject', []) or []
    except Exception:
        return [] 

def modify_tags_on_file(filepath, tags, mode='merge'):
    """
    Core "engine" function to add, remove, or overwrite tags on a file.
    Modes:
      - 'merge': Adds tags, ensuring no duplicates.
      - 'remove': Removes specified tags.
      - 'overwrite': Replaces all existing tags with new ones.
      
    Returns (success_bool, final_tags_list)
    """
    try:
        img = pyexiv2.Image(str(filepath))
        xmp_data = img.read_xmp()
        existing_tags_set = set(xmp_data.get('Xmp.dc.subject', []) or [])
        tags_set = set(tags)
        
        if mode == 'merge':
            updated_tags_set = existing_tags_set | tags_set
        elif mode == 'remove':
            updated_tags_set = existing_tags_set - tags_set
        elif mode == 'overwrite':
            updated_tags_set = tags_set
        else:
            raise ValueError(f"Unknown mode: {mode}")
            
        updated_tags = sorted(list(updated_tags_set))
        img.modify_xmp({'Xmp.dc.subject': updated_tags})
        img.close()
        
        return (True, updated_tags)
        
    except Exception as e:
        print(f"  [!] Error writing to {filepath.name}: {e}", file=sys.stderr)
        return (False, list(existing_tags_set))

# --- "FINDER" HELPER FUNCTION ---

def resolve_paths(path_str, recursive=False):
    """
    Resolves a path string (file, dir, or glob) into a list of image files.
    """
    p = Path(path_str)
    files_found = []
    
    if '*' in path_str:
        # It's a glob
        for f in glob(path_str, recursive=recursive):
            if Path(f).suffix.lower() in SUPPORTED_EXTS:
                files_found.append(Path(f))
    elif p.is_dir():
        # It's a directory
        if recursive:
            for root, dirs, files in os.walk(p):
                for file in files:
                    if Path(file).suffix.lower() in SUPPORTED_EXTS:
                        files_found.append(Path(root) / file)
        else:
            # Not recursive
            for f in p.iterdir():
                if f.is_file() and f.suffix.lower() in SUPPORTED_EXTS:
                    files_found.append(f)
    elif p.is_file():
        # It's a single file
        if p.suffix.lower() in SUPPORTED_EXTS:
            files_found.append(p)
            
    return files_found

# --- COMMAND IMPLEMENTATION: ADD ---

def cmd_add(args):
    """Logic for 'add' command."""
    print(f"Resolving path: {args.path}")
    filepaths = resolve_paths(args.path, args.recursive)
    tags_to_add = args.tags
    
    if not filepaths:
        print(f"No valid image files found for target: {args.path}")
        return
        
    print(f"Found {len(filepaths)} image(s). Adding tags: {tags_to_add}")
    
    success_count = 0
    for path in filepaths:
        success, final_tags = modify_tags_on_file(path, tags_to_add, mode='merge')
        if success:
            print(f"  [✓] {path.name}: {final_tags}")
            success_count += 1
            
    print(f"\nSummary: Successfully tagged {success_count}/{len(filepaths)} images")

# --- COMMAND IMPLEMENTATION: REMOVE ---

def cmd_remove(args):
    """Logic for 'remove' command."""
    filepaths = resolve_paths(args.path, args.recursive)
    
    if not filepaths:
        print(f"No valid image files found for target: {args.path}")
        return

    if args.all:
        mode = 'overwrite'
        tags = []
        print(f"Found {len(filepaths)} image(s). Removing ALL tags.")
    else:
        mode = 'remove'
        tags = args.tags
        print(f"Found {len(filepaths)} image(s). Removing tags: {tags}")

    success_count = 0
    for path in filepaths:
        success, final_tags = modify_tags_on_file(path, tags, mode=mode)
        if success:
            print(f"  [✓] {path.name}: {final_tags}")
            success_count += 1
            
    print(f"\nSummary: Successfully modified {success_count}/{len(filepaths)} images")

# --- COMMAND IMPLEMENTATION: READ ---

def cmd_read(args):
    """Logic for 'read' command."""
    filepaths = resolve_paths(args.path, args.recursive)
    
    if not filepaths:
        print(f"No valid image files found for target: {args.path}")
        return

    output_data = []
    
    # Header for CSV
    if args.format == 'csv':
        output_data.append(["filename", "tags"])

    for path in filepaths:
        tags = get_tags_from_file(path)
        tag_string = ",".join(tags)
        
        if args.format == 'csv':
            output_data.append([path.name, tag_string])
        elif args.format == 'txt':
            output_data.append("\n".join(tags))
        else: # console
            print(f"{path.name}: {tag_string}")

    # Write to file if --output is specified
    if args.output:
        try:
            with open(args.output, 'w', encoding='utf-8', newline='') as f:
                if args.format == 'csv':
                    writer = csv.writer(f)
                    writer.writerows(output_data)
                else: # txt
                    f.write("\n".join(output_data))
            print(f"[✓] Output saved to: {args.output}")
        except IOError as e:
            print(f"Error writing file: {e}")

# --- COMMAND IMPLEMENTATION: AUTO-TAG ---

def cmd_auto_tag(args):
    """Logic for 'auto-tag' command. (Depends on modify_tags_on_file)"""
    root_dir = Path(args.path).resolve()
    if not root_dir.exists():
        sys.exit(f"Error: Directory '{root_dir}' not found.")

    if args.dry_run:
        print(f"[AUTO-TAG] DRY-RUN: Scanning {root_dir} recursively...")
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
        try:
            relative_path = img_path.relative_to(root_dir)
        except ValueError:
            continue
            
        parts = list(relative_path.parent.parts)
        generated_tags = []

        if parts:
            if args.max_depth and len(parts) > args.max_depth:
                parts = parts[:args.max_depth]
            current_chain = ""
            for part in parts:
                current_chain_part = part.lower() 
                current_chain = f"{current_chain}/{current_chain_part}" if current_chain else current_chain_part
                generated_tags.append(current_chain)

        if args.tags_from_filename:
            stem = img_path.stem
            tokens = re.split('[-_]', stem)
            for token in tokens:
                if token and len(token) > 2:
                    generated_tags.append(token.lower())
        
        if not generated_tags:
            continue
            
        all_tag_chains.add(tuple(generated_tags))
        processed_images += 1
        print(f"  {relative_path}")
        
        if args.dry_run:
            print(f"    Tags (Dry Run): {generated_tags}")
        else:
            # USE THE "ENGINE" FUNCTION
            success, final_tags = modify_tags_on_file(img_path, generated_tags, mode='merge')
            if success:
                print(f"    Tags: {final_tags}")
                total_tags_added += len(generated_tags)
            
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
    """Logic for 'list-tags' command. (Depends on get_tags_from_file)"""
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
                
                # USE THE "ENGINE" FUNCTION
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
    else:
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

    # --- Add Parser ---
    add_parser = subparsers.add_parser('add', help='Add tags to images')
    add_parser.add_argument('path', help='File, glob, or folder to tag')
    add_parser.add_argument('tags', nargs='+', help='Tags to add')
    add_parser.add_argument('--recursive', '-r', action='store_true', help='Apply recursively if path is a folder')
    add_parser.set_defaults(func=cmd_add)
    
    # --- Remove Parser ---
    remove_parser = subparsers.add_parser('remove', help='Remove tags from images')
    remove_parser.add_argument('path', help='File, glob, or folder to modify')
    remove_parser.add_argument('tags', nargs='*', help='Specific tags to remove (omit if using --all)')
    remove_parser.add_argument('--all', action='store_true', help='Remove all tags from images')
    remove_parser.add_argument('--recursive', '-r', action='store_true', help='Apply recursively if path is a folder')
    remove_parser.set_defaults(func=cmd_remove)

    # --- Read Parser ---
    read_parser = subparsers.add_parser('read', help='Read tags from images')
    read_parser.add_argument('path', help='File, glob, or folder to read')
    read_parser.add_argument('--recursive', '-r', action='store_true', help='Apply recursively if path is a folder')
    read_parser.add_argument('--output', help='Output file path (optional)')
    read_parser.add_argument('--format', choices=['console', 'txt', 'csv'], default='console', help='Output format')
    read_parser.set_defaults(func=cmd_read)

    # --- List Tags Parser ---
    list_parser = subparsers.add_parser('list-tags', help='List all distinct tags in collection')
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
    auto_tag_parser.add_argument('--tags-from-filename', action='store_true', help='Also create tags from filename (splitting by - and _)')
    auto_tag_parser.set_defaults(func=cmd_auto_tag)
    
    # --- Run ---
    args = parser.parse_args()
    
    # Validation for 'remove' command
    if args.command == 'remove' and not args.all and not args.tags:
        remove_parser.error("You must specify tags to remove, or use --all")
    
    args.func(args)