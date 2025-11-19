# **Image Tagger**

## members:
- Syed Hanzala Ali (24k-0025)
- Rafay Siddiqui (24k-0009)

Lightweight, offline CLI tool for managing image collections through embedded XMP metadata tags.

---

## **Features**

- ✅ **Portable:** Tags embedded in images, not databases
- ✅ **Offline:** No internet or cloud required
- ✅ **Non-destructive:** Original images never moved
- ✅ **Cross-platform:** Windows, macOS, Linux

---

## **Installation**

```bash
# Clone repository
git clone https://github.com/yourusername/image-tagger.git
cd image-tagger

# Install dependencies
pip install py3exiv2

# Verify installation
python tagger.py --help
```

---

## **Quick Start**

```bash
# Tag an image
python tagger.py add photos/vacation.jpg travel beach sunset

# List all tags
python tagger.py list-tags photos/

# Export tags to CSV
python tagger.py export photos/ --output backup.csv

# Create collection from file list
python tagger.py collect photos/ selected.txt collections/favorites/
```

---

## **Command Reference**

### **1. Add Tags**

Add custom tags to images.

```bash
# Single image
python tagger.py add photos/image.jpg nature landscape 4k

# Multiple images
python tagger.py add photos/*.jpg wallpaper

# Recursive (all images in folder)
python tagger.py add photos/Nature/ --recursive nature
```

**Output:**
```
[✓] Added tags to image.jpg: ['nature', 'landscape', '4k']
[✓] Added tags to sunset.jpg: ['wallpaper']
Summary: Successfully tagged 2 images
```

---

### **2. Remove Tags**

Remove specific or all tags from images.

```bash
# Remove specific tags
python tagger.py remove photos/image.jpg old_tag unwanted

# Remove all tags
python tagger.py remove photos/image.jpg --all

# Remove from multiple images
python tagger.py remove photos/*.jpg deprecated_tag
```

**Output:**
```
[✓] Removed tags from image.jpg: ['old_tag', 'unwanted']
Remaining tags: ['nature', 'landscape']
```

---

### **3. Read Tags**

Display tags from image(s).

```bash
# Single image (console)
python tagger.py read photos/image.jpg

# Export to text file
python tagger.py read photos/image.jpg --output tags.txt

# Export to CSV
python tagger.py read photos/image.jpg --format csv --output tags.csv

# Multiple images
python tagger.py read photos/*.jpg --output all_tags.csv --format csv
```

**Console Output:**
```
image.jpg: nature, landscape, 4k
```

**tags.txt:**
```
nature
landscape
4k
```

**tags.csv:**
```csv
filename,tags
image.jpg,"nature,landscape,4k"
```

---

### **4. List All Tags**

Show all distinct tags across collection.

```bash
# Basic list (console)
python tagger.py list-tags photos/

# With image counts
python tagger.py list-tags photos/ --counts

# Sort by popularity
python tagger.py list-tags photos/ --counts --sort count

# Export to text file
python tagger.py list-tags photos/ --output all_tags.txt

# Export to CSV with counts
python tagger.py list-tags photos/ --output tags.csv --format csv
```

**Console Output:**
```
All distinct tags:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
4k                 (12 images)
beach              (8 images)
landscape          (15 images)
nature             (18 images)
travel             (10 images)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total: 5 distinct tags
```

**tags.csv:**
```csv
tag,count
4k,12
beach,8
landscape,15
nature,18
travel,10
```

---

### **5. Auto-tag from Folders**

One-time migration: generate hierarchical tags from folder structure.

```bash
# Auto-tag all images
python tagger.py auto-tag photos/

# Preview without applying
python tagger.py auto-tag photos/ --dry-run

# Limit hierarchy depth
python tagger.py auto-tag photos/ --max-depth 2
```

**Example:**
```
Before: photos/Wallpapers/Nature/Mountains/peak.jpg
After:  Tags: [wallpapers, wallpapers/nature, wallpapers/nature/mountains]
```

**Output:**
```
[AUTO-TAG] Scanning photos/ recursively...
Found 88 images in 15 folders

Processing:
  [✓] photos/Wallpapers/Nature/peak.jpg
      Tags: [wallpapers, wallpapers/nature]
  
Summary:
  • Images processed: 88
  • Unique tag chains: 11
  • Average tags per image: 2.1
```

**auto-tag with file name**

Auto-Tag with Filename (New Behavior)

When you add the new `--tags-from-filename` flag, the script will:

1. Get folder tags: ['ireland']

2. Analyze filename `20230317-BallyvooneyCove_ROW5905528136_UHD:`

```
    20230317: kept -> 20230317
    BallyvooneyCove: Kept -> ballyvooneycove
    UHD: Kept -> uhd
    ROW5905528136: kept -> ROW5905528136
    Merge them all.
```
---

### **6. Export Tags**

Export all image paths and tags to CSV.

```bash
# Export all tags
python tagger.py export photos/ --output all_tags.csv

# Export with relative paths
python tagger.py export photos/ --output tags.csv --relative

# Export specific folder (no recursion)
python tagger.py export photos/Wallpapers/ --output wallpapers.csv --no-recursive
```

**all_tags.csv:**
```csv
filepath,tags
photos/Wallpapers/Nature/image1.jpg,"wallpapers,wallpapers/nature,4k"
photos/Personal/Travel/beach.jpg,"personal,personal/travel,beach,sunset"
photos/Projects/logo.jpg,"projects,branding"
```

---

### **7. Import Tags**

Restore or apply tags from CSV backup.

```bash
# Import and merge with existing tags (default)
python tagger.py import tags.csv

# Import and overwrite existing tags
python tagger.py import tags.csv --mode overwrite

# Import only to untagged images
python tagger.py import tags.csv --mode add-only

# Preview import
python tagger.py import tags.csv --dry-run
```

**Output:**
```
[IMPORT-CSV] Reading tags.csv...
Found 88 entries

Import Strategy: MERGE (add to existing tags)

Preview:
  photos/image1.jpg
    Current: [travel, personal]
    Adding: [wallpapers, 4k]
    Result: [travel, personal, wallpapers, 4k]

Proceed? (y/n): y

[✓] Import complete
    Images updated: 88
    Tags added: 156
```

---

### **8. Validate CSV**

Verify CSV format and file integrity.

```bash
# Validate CSV
python tagger.py validate tags.csv

# Detailed report
python tagger.py validate tags.csv --detailed

# Export validation report
python tagger.py validate tags.csv --output report.txt
```

**Output:**
```
[VALIDATE-CSV] Checking tags.csv...

Format Validation:
  [✓] Header row present
  [✓] Correct columns
  [✓] UTF-8 encoding

File Path Validation:
  [✓] 85 files found (96.6%)
  [⚠] 3 files not found

Tag Validation:
  [✓] 15 unique tags
  [✓] No invalid characters

Status: VALID WITH WARNINGS
```

---

### **9. Create Collection**

Create new folder from filename list (searches root folder recursively).

```bash
# Create collection from text file
python tagger.py collect photos/ selected.txt collections/favorites/

# Preview collection
python tagger.py collect photos/ selected.txt collections/favorites/ --dry-run

# Handle duplicate filenames
python tagger.py collect photos/ selected.txt collections/favorites/ --duplicates [first|all|skip]

# Use symlinks (save space)
python tagger.py collect photos/ selected.txt collections/favorites/ --symlinks
```

**selected.txt:**
```
image1.jpg
sunset.png
vacation.jpg
```

**Output:**
```
[CREATE-COLLECTION] Searching for 3 files in photos/...

Found: 3 files (100%)
  ✓ image1.jpg → photos/Wallpapers/Nature/image1.jpg
  ✓ sunset.png → photos/Personal/Travel/sunset.png
  ✓ vacation.jpg → photos/Summer/vacation.jpg

Creating collection...
[✓] Collection created!
    Location: collections/favorites/
    Files: 3
    Size: 24.5 MB
```

---

### **10. Find Files**

Search for files by name across root folder.

```bash
# Find specific files
python tagger.py find photos/ image1.jpg sunset.png

# Find from file list
python tagger.py find photos/ --files search.txt

# Export found paths
python tagger.py find photos/ --files search.txt --output found.txt

# Export to CSV
python tagger.py find photos/ --files search.txt --format csv --output found.csv
```

**Console Output:**
```
Searching for 3 files in photos/...

Found:
  ✓ image1.jpg → photos/Wallpapers/Nature/image1.jpg
  ✓ sunset.png → photos/Personal/Travel/sunset.png
  ✗ missing.jpg → NOT FOUND

Results: 2 found, 1 missing
```

**found.csv:**
```csv
filename,found,path
image1.jpg,true,photos/Wallpapers/Nature/image1.jpg
sunset.png,true,photos/Personal/Travel/sunset.png
missing.jpg,false,
```

---

### **11. List Files**

List all images in folder.

```bash
# List all images (console)
python tagger.py list-files photos/

# Export to text file
python tagger.py list-files photos/ --output all_files.txt

# Export with full paths
python tagger.py list-files photos/ --full-paths --output files.txt

# Export to CSV
python tagger.py list-files photos/ --format csv --output files.csv
```

**Console Output:**
```
Found 88 images in photos/:
  image1.jpg
  image2.png
  subfolder/vacation.jpg
  ...
```

**files.csv:**
```csv
filename,path,size_bytes,format
image1.jpg,photos/Wallpapers/Nature/image1.jpg,4523890,JPEG
image2.png,photos/Personal/image2.png,2341567,PNG
```

---

### **12. Sort by Tags**

Create temporary tag-based sorted folder views.

```bash
# Create sorted views
python tagger.py sort photos/

# Preserve folder hierarchy
python tagger.py sort photos/ --preserve-hierarchy

# Clear and re-sort
python tagger.py sort photos/ --clear

# Sort specific tags only
python tagger.py sort photos/ --tags wallpapers nature
```

**Output:**
```
[SORT] Scanning photos/ recursively...
Found 88 images

Creating sorted structure:
  ├─ sorted/nature/         (18 images)
  ├─ sorted/wallpapers/     (12 images)
  ├─ sorted/travel/         (10 images)
  └─ sorted/beach/          (8 images)

[✓] Sorted view created at: photos/sorted/
```

**Result:**
```
photos/
├── image1.jpg (original)
├── image2.png (original)
└── sorted/
    ├── nature/
    │   ├── image1.jpg (copy)
    │   └── image3.jpg (copy)
    └── wallpapers/
        └── image1.jpg (copy)
```

---

### **13. Remove Sorted Folders**

Remove temporary sorted folders.

```bash
# Remove sorted folders
python tagger.py unsort photos/

# Preview what will be deleted
python tagger.py unsort photos/ --dry-run
```

**Output:**
```
[UNSORT] Removing sorted folders from photos/...

Found sorted folder: photos/sorted/
  Contains: 7 subfolders, 88 files (duplicates)

Remove? (y/n): y

[✓] Sorted folders removed
    Freed: 156.8 MB
```

---

### **14. Verify Metadata**

Check metadata integrity across collection.

```bash
# Verify all images
python tagger.py verify photos/

# Verify and attempt repair
python tagger.py verify photos/ --repair

# Export verification report
python tagger.py verify photos/ --output report.txt

# Export to CSV
python tagger.py verify photos/ --format csv --output report.csv
```

**Console Output:**
```
Verifying metadata in photos/...

✓ Valid: 85 images (96.6%)
⚠ Warnings: 2 images (2.3%)
  - corrupted.jpg: Metadata corrupted
  - old_file.png: No XMP metadata

✗ Errors: 1 image (1.1%)
  - broken.jpg: Cannot read file

Summary: 87/88 readable (98.9%)
```

**report.csv:**
```csv
filepath,status,issue
photos/image1.jpg,valid,
photos/corrupted.jpg,warning,Metadata corrupted
photos/broken.jpg,error,Cannot read file
```

---

### **15. Basic Statistics**

Show collection statistics.

```bash
# Basic stats (console)
python tagger.py stats photos/

# Detailed stats
python tagger.py stats photos/ --detailed

# Export stats
python tagger.py stats photos/ --output stats.txt

# Export to CSV
python tagger.py stats photos/ --format csv --output stats.csv
```

**Console Output:**
```
Statistics for photos/:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Files:
  Total images: 88
  Total size: 1.2 GB
  Average size: 14.3 MB

Formats:
  JPG:  64 (72.7%)
  PNG:  18 (20.5%)
  WEBP:  6 (6.8%)

Tags:
  Images with tags: 85 (96.6%)
  Images without tags: 3 (3.4%)
  Distinct tags: 15
  Avg tags per image: 2.8
```

**stats.csv:**
```csv
metric,value
total_images,88
total_size_bytes,1288490188
total_size_mb,1228.8
avg_size_mb,14.3
format_jpg,64
format_png,18
format_webp,6
images_with_tags,85
images_without_tags,3
distinct_tags,15
avg_tags_per_image,2.8
```

---

## **Common Workflows**

### **Workflow 1: Initial Setup**

```bash
# 1. One-time auto-tag from existing folder structure
python tagger.py auto-tag photos/

# 2. Add manual tags
python tagger.py add photos/favorites/*.jpg favorite

# 3. Export backup
python tagger.py export photos/ --output backup_$(date +%Y%m%d).csv

# 4. Create sorted views for browsing
python tagger.py sort photos/
```

---

### **Workflow 2: Query & Collect**

```bash
# 1. Export all tags
python tagger.py export photos/ --output all_tags.csv

# 2. External analysis (filter CSV, create file list)
# ... user or external script processes CSV ...

# 3. Create collection from results
python tagger.py collect photos/ selected.txt collections/beach_sunsets/
```

---

### **Workflow 3: Backup & Restore**

```bash
# Create backup
python tagger.py export photos/ --output backup.csv

# Simulate disaster: all tags lost
# ... tags somehow deleted ...

# Restore from backup
python tagger.py import backup.csv --mode overwrite

# Verify restoration
python tagger.py verify photos/
```

---

## **CSV Formats**

### **Tag Export (from `export` command):**
```csv
filepath,tags
photos/image1.jpg,"wallpapers,nature,4k"
photos/image2.png,"personal,travel,beach"
```

### **Tag List with Counts (from `list-tags --format csv`):**
```csv
tag,count
nature,18
wallpapers,12
travel,10
beach,8
4k,12
```

### **File List (from `list-files --format csv`):**
```csv
filename,path,size_bytes,format
image1.jpg,photos/Wallpapers/Nature/image1.jpg,4523890,JPEG
image2.png,photos/Personal/image2.png,2341567,PNG
```

### **Verification Report (from `verify --format csv`):**
```csv
filepath,status,issue
photos/image1.jpg,valid,
photos/corrupted.jpg,warning,Metadata corrupted
photos/broken.jpg,error,Cannot read file
```

### **Collection Input (for `collect` command):**
```
image1.jpg
sunset.png
vacation.jpg
```
or
```csv
filename
image1.jpg
sunset.png
vacation.jpg
```

---

## **Configuration**

Optional `tagger.config.yaml` for defaults:

```yaml
# Default settings
auto_tag:
  max_depth: null
  normalize_case: lowercase
  replace_spaces: true

sort:
  collision_strategy: rename
  preserve_hierarchy: false

collection:
  duplicates_mode: first
  use_symlinks: false
```

---

## **Supported Formats**

- JPEG (`.jpg`, `.jpeg`)
- PNG (`.png`)
- WebP (`.webp`)
- TIFF (`.tiff`, `.tif`)

---

## **Requirements**

- Python 3.10+
- `py3exiv2` library


## **FAQ**

**Q: Where are tags stored?**  
A: In XMP metadata (`Xmp.dc.subject` field) embedded in image files.

**Q: Are original images modified?**  
A: Only metadata is modified. Image data is never changed. Sorted folders contain copies.

**Q: Can I use this with Lightroom/other tools?**  
A: Yes! XMP tags are standard and readable by Adobe products and most image software.

**Q: What if I have duplicate filenames in different folders?**  
A: `collect` command has `--duplicates` flag: `first` (default), `all`, or `skip`.

**Q: Can I run this on Windows?**  
A: Yes. Use backslashes or forward slashes for paths: `python tagger.py list-tags C:\Photos\`

**Q: How do I query by complex criteria?**  
A: Export to CSV, then use external tools (pandas, Excel, R) to filter. Then use `collect` to create collections from results.

---
