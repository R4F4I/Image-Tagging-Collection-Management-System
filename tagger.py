#!/usr/bin/env python3
"""
Image Tagger CLI
Lightweight, offline tool for managing image collections 
through embedded XMP metadata tags.
"""

import os
import sys
import re
import csv
import glob
import argparse
from pathlib import Path
from collections import Counter

# Try importing the library, handle error if missing
try:
    import pyexiv2
except ImportError:
    sys.exit("Error: pyexiv2 not found. Install it via 'pip install pyexiv2'")
except RuntimeError as e:
    sys.exit(f"Error importing pyexiv2: {e}\nTry reinstalling 'pyexiv2'.")

SUPPORTED_EXTS = {'.jpg', '.jpeg', '.png', '.webp', '.tif', '.tiff'}

# --- CORE METADATA ENGINE ---

def _get_long_path_str(filepath):
    """
    Returns a Windows-compatible long path string (e.g., \\?\)
    if on Windows. Otherwise, returns the original path string.
    """
    path_str = str(filepath)
    if os.name == 'nt':
        # Use Windows long path prefix
        return "\\\\?\\" + path_str
    return path_str

def get_tags_from_file(filepath):
    """
    Safely extracts XMP tags (Xmp.dc.subject) from a single file.
    Returns a list of tags.
    """
    try:
        path_str = _get_long_path_str(filepath)
        img = pyexiv2.Image(path_str)
        metadata = img.read_xmp()
        img.close()
        
        tag_key = 'Xmp.dc.subject'
        if tag_key in metadata:
            return metadata[tag_key] # pyexiv2 returns a list
        else:
            return []
    except Exception as e:
        print(f"[!] Warning: Could not read {filepath.name}: {e}", file=sys.stderr)
        return []

def modify_tags_on_file(filepath, tags_to_process, mode='merge'):
    """
    Core engine function to add, remove, or overwrite tags on a file.

    Args:
        filepath (Path): The image file.
        tags_to_process (list): The list of tags to add/remove.
        mode (str): 
            'merge' (default): Add new tags, ensuring no duplicates.
            'remove': Remove specified tags.
            'overwrite': Erase all old tags and replace with new ones.

    Returns:
        (bool, list): (Success, final_list_of_tags)
    """
    existing_tags_set = set()
    try:
        path_str = _get_long_path_str(filepath)
        
        # 1. Read existing tags
        # We must use 'with' or 'img.close()' to release the file lock
        try:
            img_read = pyexiv2.Image(path_str)
            metadata = img_read.read_xmp()
            img_read.close()
            
            tag_key = 'Xmp.dc.subject'
            if tag_key in metadata:
                existing_tags_set = set(metadata[tag_key])
        except Exception:
            pass # File might be new or unreadable, start with empty set

        new_tags_set = set(tags_to_process)

        # 2. Apply logic based on mode
        if mode == 'merge':
            final_tags_set = existing_tags_set.union(new_tags_set)
        elif mode == 'remove':
            final_tags_set = existing_tags_set.difference(new_tags_set)
        elif mode == 'overwrite':
            final_tags_set = new_tags_set
        else:
            raise ValueError(f"Unknown mode: {mode}")

        # 3. Write new tags
        # Convert set back to list for pyexiv2
        final_tags_list = sorted(list(final_tags_set))
        
        # Open in read/write mode to modify
        img_write = pyexiv2.Image(path_str)
        img_write.modify_xmp({'Xmp.dc.subject': final_tags_list})
        img_write.close()

        return (True, final_tags_list)

    except Exception as e:
        print(f"[!] Error writing to {filepath.name}: {e}", file=sys.stderr)
        # Return the original tags if modification failed
        return (False, list(existing_tags_set))

# --- FILE/PATH HELPERS ---

def resolve_paths(path_str, recursive=False):
    """
    Resolves a path string (file, dir, glob) into a list of image Paths.
    """
    path = Path(path_str).resolve()
    if path.is_file():
        if path.suffix.lower() in SUPPORTED_EXTS:
            return [path]
        return []
    
    if path.is_dir():
        if recursive:
            # Use os.walk for efficient recursive search
            image_files = []
            for root, _, files in os.walk(path):
                for file in files:
                    if Path(file).suffix.lower() in SUPPORTED_EXTS:
                        image_files.append(Path(root) / file)
            return image_files
        else:
            # Non-recursive, just this directory
            return [f for f in path.iterdir() if f.suffix.lower() in SUPPORTED_EXTS]
    
    # If not a file or dir, try as glob
    # Note: glob.glob is non-recursive by default
    image_files = []
    for f_name in glob.glob(str(path)): # Use resolved path for glob
        f_path = Path(f_name)
        if f_path.suffix.lower() in SUPPORTED_EXTS:
            image_files.append(f_path)
    
    if not image_files:
        print(f"Warning: No files matched '{path_str}'", file=sys.stderr)
        
    return image_files


# --- COMMAND FUNCTIONS ---

def cmd_add(args):
    """Logic for 'add' command. (Depends on resolve_paths, modify_tags_on_file)"""
    image_files = resolve_paths(args.path, args.recursive)
    tags_to_add = args.tags
    
    if not image_files:
        print("No images found to tag.")
        return
        
    print(f"Adding tags {tags_to_add} to {len(image_files)} image(s)...")
    success_count = 0
    
    for f in image_files:
        success, final_tags = modify_tags_on_file(f, tags_to_add, mode='merge')
        if success:
            success_count += 1
            print(f"  [✓] {f.name}: {final_tags}")
        else:
            print(f"  [✗] {f.name}: Failed")
            
    print(f"\nSummary: Successfully tagged {success_count}/{len(image_files)} images.")

def cmd_remove(args):
    """Logic for 'remove' command. (Depends on resolve_paths, modify_tags_on_file)"""
    image_files = resolve_paths(args.path, args.recursive)
    
    if not image_files:
        print("No images found to modify.")
        return

    success_count = 0
    
    if args.all:
        print(f"Removing ALL tags from {len(image_files)} image(s)...")
        for f in image_files:
            success, final_tags = modify_tags_on_file(f, [], mode='overwrite')
            if success:
                success_count += 1
                print(f"  [✓] {f.name}: All tags removed.")
            else:
                print(f"  [✗] {f.name}: Failed")
    else:
        tags_to_remove = args.tags
        if not tags_to_remove:
            print("Error: No tags specified to remove. Use --all to remove all tags.")
            return
            
        print(f"Removing tags {tags_to_remove} from {len(image_files)} image(s)...")
        for f in image_files:
            success, final_tags = modify_tags_on_file(f, tags_to_remove, mode='remove')
            if success:
                success_count += 1
                print(f"  [✓] {f.name}: {final_tags}")
            else:
                print(f"  [✗] {f.name}: Failed")
            
    print(f"\nSummary: Successfully modified {success_count}/{len(image_files)} images.")

def cmd_read(args):
    """Logic for 'read' command. (Depends on resolve_paths, get_tags_from_file)"""
    image_files = resolve_paths(args.path, args.recursive)
    
    if not image_files:
        print("No images found to read.")
        return

    output_lines = []
    
    if args.format == 'csv':
        output_lines.append("filename,tags")
        
    for f in image_files:
        tags = get_tags_from_file(f)
        tags_str = ",".join(tags)
        
        if args.format == 'csv':
            output_lines.append(f'"{f.name}","{tags_str}"')
        else: # txt/console
            output_lines.append(f"{f.name}: {tags_str}")

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

def cmd_list_tags(args):
    """Logic for 'list-tags' command. (Depends on get_tags_from_file)"""
    target_dir = Path(args.path).resolve() # Resolve to absolute path
    if not target_dir.exists():
        sys.exit(f"Error: Directory '{target_dir}' not found.")

    print(f"Scanning {target_dir} for tags...")
    
    tag_counts = Counter()
    total_images = 0
    tagged_images = 0

    # Recursive Scan
    for root, dirs, files in os.walk(target_dir):
        for file in files:
            if Path(file).suffix.lower() in SUPPORTED_EXTS:
                full_path = Path(root) / file
                total_images += 1
                
                tags = get_tags_from_file(full_path)
                if tags:
                    tagged_images += 1
                    tag_counts.update(tags)

    # Sorting Logic
    sorted_tags = list(tag_counts.items())
    
    if args.sort == 'count':
        sorted_tags.sort(key=lambda x: (-x[1], x[0]))
    else:
        sorted_tags.sort(key=lambda x: x[0])

    # Output Formatting
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

    # Write Output
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
            individual_parts_tags = set()
            hierarchical_tags = []

            for part in parts:
                part_lower = part.lower()
                
                # 1. Add individual tag (e.g., 'a', 'b', 'c')
                individual_parts_tags.add(part_lower)
                
                # 2. Build and add hierarchical tag (e.g., 'a', 'a/b', 'a/b/c')
                current_chain = f"{current_chain}/{part_lower}" if current_chain else part_lower
                hierarchical_tags.append(current_chain)
            
            generated_tags.extend(list(individual_parts_tags))
            generated_tags.extend(hierarchical_tags)

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
            print(f"    Tags (Dry Run): {sorted(list(set(generated_tags)))}")
        else:
            # USE THE "ENGINE" FUNCTION
            success, final_tags = modify_tags_on_file(img_path, generated_tags, mode='merge')
            if success:
                print(f"    Tags: {final_tags}")
                total_tags_added += len(set(generated_tags).difference(set(get_tags_from_file(img_path))))
            
    avg_tags = (total_tags_added / processed_images) if processed_images > 0 else 0
    print("\nSummary:")
    print(f"  • Images processed: {processed_images}")
    print(f"  • Unique tag chains: {len(all_tag_chains)}")
    if not args.dry_run:
        print(f"  • Total tags added: {total_tags_added}")
        print(f"  • Average tags per image: {avg_tags:.1f}")
    if args.dry_run:
        print("\nDRY-RUN complete. No files were changed.")

def cmd_export(args):
    """Logic for 'export' command. (Depends on resolve_paths, get_tags_from_file)"""
    scan_path = Path(args.path).resolve() # Resolve to absolute path to prevent errors
    if not scan_path.exists():
        sys.exit(f"Error: Path '{scan_path}' not found.")

    # The --no-recursive flag is the inverse of the recursive parameter
    is_recursive = not args.no_recursive
    
    image_files = resolve_paths(args.path, recursive=is_recursive)

    if not image_files:
        print("No images found to export.")
        return

    print(f"Found {len(image_files)} images. Exporting to {args.output}...")

    try:
        with open(args.output, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['filepath', 'tags'])

            for img_path in image_files:
                tags = get_tags_from_file(img_path)
                tags_str = ",".join(tags)

                # Determine the path to write based on the --relative flag
                if args.relative and scan_path.is_dir():
                    try:
                        # Make path relative to the initial scan directory
                        display_path = img_path.relative_to(scan_path.resolve())
                    except ValueError:
                        display_path = img_path # Fallback if not a subpath
                else:
                    display_path = img_path

                writer.writerow([str(display_path).replace('\\', '/'), tags_str])

        print(f"[✓] Successfully exported data for {len(image_files)} images to {args.output}")

    except IOError as e:
        sys.exit(f"Error writing to file '{args.output}': {e}")


# --- MAIN CLI ROUTER ---

def main():
    parser = argparse.ArgumentParser(
        description="Lightweight, offline CLI tool for managing image collections through embedded XMP metadata tags.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    subparsers = parser.add_subparsers(dest='command', required=True, help="Available commands")

    # 1. Add Tags
    add_parser = subparsers.add_parser('add', help='Add tags to images.')
    add_parser.add_argument('path', help='File, directory, or glob pattern (e.g., "photos/*.jpg")')
    add_parser.add_argument('tags', nargs='+', help='One or more tags to add (e.g., nature landscape)')
    add_parser.add_argument('-r', '--recursive', action='store_true', help='Recursively search directories.')
    add_parser.set_defaults(func=cmd_add)

    # 2. Remove Tags
    remove_parser = subparsers.add_parser('remove', help='Remove tags from images.')
    remove_parser.add_argument('path', help='File, directory, or glob pattern.')
    remove_parser.add_argument('tags', nargs='*', help='One or more tags to remove. (Omit for --all)')
    remove_parser.add_argument('--all', action='store_true', help='Remove all tags from the image(s).')
    remove_parser.add_argument('-r', '--recursive', action='store_true', help='Recursively search directories.')
    remove_parser.set_defaults(func=cmd_remove)

    # 3. Read Tags
    read_parser = subparsers.add_parser('read', help='Read and display tags from image(s).')
    read_parser.add_argument('path', help='File, directory, or glob pattern.')
    read_parser.add_argument('-r', '--recursive', action='store_true', help='Recursively search directories.')
    read_parser.add_argument('--output', help='Export tags to a file (e.g., tags.txt or tags.csv)')
    read_parser.add_argument('--format', choices=['txt', 'csv'], default='txt', help='Output format (default: txt)')
    read_parser.set_defaults(func=cmd_read)
    
    # 4. List All Tags
    list_parser = subparsers.add_parser('list-tags', help='List all distinct tags in a collection.')
    list_parser.add_argument('path', help='Root directory to scan.')
    list_parser.add_argument('--counts', action='store_true', help='Show image counts per tag.')
    list_parser.add_argument('--sort', choices=['alpha', 'count'], default='alpha', help='Sort order (default: alpha)')
    list_parser.add_argument('--output', help='Export list to a file (e.g., tags.txt or tags.csv)')
    list_parser.add_argument('--format', choices=['txt', 'csv'], default='txt', help='Output format (default: txt)')
    list_parser.set_defaults(func=cmd_list_tags)

    # 5. Auto-tag from Folders
    auto_parser = subparsers.add_parser('auto-tag', help='Generate hierarchical tags from folder structure.')
    auto_parser.add_argument('path', help='Root directory to scan and tag.')
    auto_parser.add_argument('--dry-run', action='store_true', help='Preview changes without writing any tags.')
    auto_parser.add_argument('--max-depth', type=int, help='Limit folder hierarchy depth (e.g., 2 for a/b)')
    auto_parser.add_argument('--tags-from-filename', action='store_true', help='Add tags from filename (split by - or _)')
    auto_parser.set_defaults(func=cmd_auto_tag)

    # 6. Export Tags
    export_parser = subparsers.add_parser('export', help='Export all image paths and tags to a CSV file.')
    export_parser.add_argument('path', help='Root directory or path to scan.')
    export_parser.add_argument('--output', required=True, help='Output CSV file path (e.g., all_tags.csv).')
    export_parser.add_argument('--relative', action='store_true', help='Use paths relative to the input directory.')
    export_parser.add_argument('--no-recursive', action='store_true', help='Disable recursive scanning of directories.')
    export_parser.set_defaults(func=cmd_export)

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
        
    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()