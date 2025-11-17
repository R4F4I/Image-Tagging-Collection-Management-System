# **Image Tagging & Collection Management System**
## **Offline, Metadata-Driven Photo Organization**

---

## **1. Project Overview**

This project delivers a **lightweight, CLI-based Python tool** for organizing image collections through **embedded metadata tags**. Unlike database-dependent solutions or cloud services, all tags are stored directly in image files using **XMP metadata standards**, ensuring complete portability and offline operation.

### **Core Philosophy**
- **Non-destructive:** Original images never move from their root folder
- **Portable:** Tags embedded in images, readable by any XMP-compatible software
- **Offline-first:** No internet, cloud, or external services required
- **Separation of concerns:** Core tool handles tagging; external scripts handle analysis

---

## **2. Problem Statement**

Photographers, designers, and digital archivists face common challenges:
- **Lost organization:** Folder structures become chaotic over time
- **Database dependency:** Traditional tools use proprietary databases that don't travel with images
- **Cloud lock-in:** Online solutions require constant connectivity and subscription fees
- **Complex tools:** Professional software (Lightroom, etc.) is expensive and over-featured for basic needs
- **Search limitations:** File systems can't search by custom attributes

**This tool solves these problems** by embedding tags directly into images while maintaining a simple, scriptable interface.

---

## **3. Key Features**

### **Phase 1: Core Operations (15 Commands)**

#### **A. Tag Management**
- **add** - Add custom tags to images
- **remove** - Remove specific or all tags
- **read** - Display tags with optional export
- **list-tags** - Show all distinct tags across collection
- **auto-tag** - One-time migration: generate tags from existing folder structure

#### **B. Import/Export**
- **export** - Create CSV backup of all images and their tags
- **import** - Restore tags from CSV backup (merge/overwrite modes)
- **validate** - Verify CSV integrity before import

#### **C. Collection Creation**
- **collect** - Create new folder from filename list (searches root folder recursively)
- **find** - Locate specific files by name across entire folder tree
- **list-files** - Export inventory of all images

#### **D. Organization**
- **sort** - Generate temporary tag-based folder views
- **unsort** - Remove temporary sorted folders

#### **E. Maintenance**
- **verify** - Check metadata integrity across collection
- **stats** - Display basic statistics (counts, sizes, formats)

---

## **4. Workflow Architecture**

### **Primary Workflow:**
```
┌─────────────────┐
│  Root Folder    │  All original images stored here
│  (photos/)      │  Images never move
└────────┬────────┘
         │
         ├──→ [1. Tag Images] ──→ Embedded XMP metadata
         │
         ├──→ [2. Export CSV] ──→ all_tags.csv (filepath, tags)
         │                         ↓
         │                    [External Analysis]
         │                    (pandas/R/Excel)
         │                         ↓
         │                    filtered_files.txt (just filenames)
         │                         ↓
         └──→ [3. Create Collection] ──→ New folder with selected images
```

### **Data Flow:**
1. **Tagging:** User tags images manually or via folder-based auto-tag
2. **Export:** Full CSV export contains all filepaths and tags
3. **External Analysis:** User or scripts query/filter the CSV (out of scope)
4. **Collection:** Script searches root folder for specified filenames and creates collection

---

## **5. Technical Specifications**

### **Technology Stack**
- **Language:** Python 3.10+
- **Core Dependency:** `pyexiv2` (XMP metadata handling)
- **Standard Libraries:** `pathlib`, `shutil`, `argparse`, `csv`
- **Optional:** `rich` (enhanced CLI output)

### **Metadata Storage**
- **Format:** XMP (Extensible Metadata Platform)
- **Field:** `Xmp.dc.subject` (Dublin Core standard)
- **Compatibility:** Adobe products, EXIF tools, image viewers
- **Portability:** Tags survive file transfers, cloud sync, OS changes

### **File Operations**
- **Supported formats:** JPG, JPEG, PNG, WEBP, TIFF
- **Collision handling:** Automatic renaming with numeric suffixes
- **Path handling:** Cross-platform (Windows, macOS, Linux)

---

## **6. Example Usage**

### **Basic Tagging**
```bash
# Tag images
python tagger.py add photos/vacation.jpg travel beach sunset
python tagger.py add photos/wallpaper.png wallpaper 4k nature

# Read tags
python tagger.py read photos/vacation.jpg
# Output: travel, beach, sunset

# List all distinct tags
python tagger.py list-tags photos/
# Output: travel, beach, sunset, wallpaper, 4k, nature
```

### **Legacy Migration**
```bash
# Auto-generate tags from existing folder structure
python tagger.py auto-tag photos/

# Before: photos/Wallpapers/Nature/Mountains/peak.jpg
# After: Tagged with [wallpapers, wallpapers/nature, wallpapers/nature/mountains]
```

### **Export & Analysis**
```bash
# Export all tags to CSV
python tagger.py export photos/ --output all_tags.csv

# CSV format:
# filepath,tags
# photos/Wallpapers/Nature/peak.jpg,"wallpapers,wallpapers/nature,4k"
# photos/Travel/beach.jpg,"travel,beach,sunset"

# External analysis (user's own script)
# Filters CSV, outputs simple filename list: selected.txt
```

### **Collection Creation**
```bash
# Create collection from filtered results
python tagger.py collect photos/ selected.txt collections/beach_sunsets/

# selected.txt (just filenames):
# beach.jpg
# sunset.jpg
# vacation.jpg

# Script searches entire photos/ tree, copies found files to collection
```

### **Temporary Sorting**
```bash
# Create tag-based sorted views
python tagger.py sort photos/

# Result:
# photos/sorted/travel/        ← copies of images tagged "travel"
# photos/sorted/beach/         ← copies of images tagged "beach"
# photos/sorted/wallpaper/     ← copies of images tagged "wallpaper"
```

---

## **7. Use Cases**

### **Use Case 1: Photographer Portfolio**
- Tag images by client, project, style
- Export CSV for client reporting
- Create collections for specific deliverables
- Sort by tag for quick browsing

### **Use Case 2: Wallpaper Curator**
- Tag by resolution, orientation, theme
- Export and analyze with custom scripts
- Generate filtered collections (e.g., "4K nature wallpapers")
- Maintain organization as collection grows

### **Use Case 3: Digital Archivist**
- One-time auto-tag from existing folder structure
- Export CSV as inventory backup
- Verify metadata integrity periodically
- Create curated collections for different audiences

---

## **8. Benefits**

### **vs. Cloud Services (Google Photos, iCloud)**
✅ Complete offline operation  
✅ No subscription fees  
✅ No file size/count limits  
✅ Full data ownership  

### **vs. Professional Software (Lightroom, ACDSee)**
✅ Free and open source  
✅ Simple, focused feature set  
✅ CLI automation capabilities  
✅ No database files to manage  

### **vs. OS File Tags (Windows/Mac)**
✅ Cross-platform compatibility  
✅ Tags embedded in files (not OS-dependent)  
✅ Hierarchical tag support  
✅ Scriptable and extensible  

### **vs. Folder-based Organization**
✅ Multi-dimensional organization (images can have multiple tags)  
✅ Flexible querying via CSV export  
✅ Searchable without moving files  
✅ Preserves original folder structure  

---

## **9. Project Scope**

### **In Scope**
- Core tagging operations (add, remove, read)
- CSV export/import for backup and portability
- Collection creation from filename lists
- Temporary tag-based sorting
- Basic verification and statistics
- CLI interface only

### **Out of Scope (External Scripts)**
- Complex tag queries (AND/OR/NOT logic)
- Statistical analysis and reporting
- AI/ML-based auto-tagging
- Duplicate image detection
- GUI interface
- Cloud integration

**Rationale:** Keeping the core tool simple and focused allows users to build custom analysis pipelines using their preferred tools (pandas, R, Excel, etc.). The CSV export provides a clean interface between tagging operations and advanced analysis.

---

## **10. Success Criteria**

### **Functional Requirements**
- ✅ Successfully tag/untag 1,000+ images in seconds
- ✅ 100% metadata portability (XMP standard compliance)
- ✅ Zero data loss (non-destructive operations only)
- ✅ Cross-platform compatibility verified

### **Performance Targets**
- List 10,000 tags in <2 seconds
- Export 10,000 images to CSV in <10 seconds
- Create collection of 100 images in <5 seconds
- Sort 1,000 images by tags in <15 seconds

### **Usability Goals**
- New user productive in <10 minutes
- Complete documentation with examples
- Consistent command structure across all operations
- Clear error messages with actionable guidance

---

## **11. Deliverables**

1. **tagger.py** - Complete CLI tool with all Phase 1 features
2. **README.md** - Installation, usage, and examples
3. **User Guide** - Detailed command reference and workflows
4. **Example Scripts** - Sample external analysis scripts (Python, R)
5. **Test Suite** - Unit tests for core operations
6. **Configuration** - Optional YAML config for defaults

---

## **12. Future Enhancements (Phase 2+)**

- Global tag renaming
- Batch tag operations from CSV
- JSON export format option
- Collection update/refresh
- Symlink mode for collections
- Auto-repair corrupted metadata
- Import from other tagging systems
