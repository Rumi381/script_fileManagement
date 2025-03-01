# File Operations Utility

A versatile command-line utility for finding and performing operations (delete, copy, move) on files and directories based on extensions, names, or various matching criteria.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Basic Usage](#basic-usage)
- [Command-line Arguments](#command-line-arguments)
  - [Required Arguments](#required-arguments)
  - [Source Options](#source-options)
  - [Target Options](#target-options)
  - [Pattern File Options](#pattern-file-options)
  - [Exclusion Options](#exclusion-options)
  - [Behavior Options](#behavior-options)
  - [Safety Options](#safety-options)
  - [Output Options](#output-options)
- [Use Cases](#use-cases)
  - [Basic File Operations](#basic-file-operations)
  - [Working with Multiple Extensions](#working-with-multiple-extensions)
  - [Using Pattern Files](#using-pattern-files)
  - [Non-recursive Operations](#non-recursive-operations)
  - [Handling Special Filenames](#handling-special-filenames)
  - [Exclusion Operations](#exclusion-operations)
  - [Directory Operations](#directory-operations)
  - [Preview Mode](#preview-mode)
  - [Backup Before Operations](#backup-before-operations)
- [Pattern File Format](#pattern-file-format)
- [Advanced Examples](#advanced-examples)
- [Troubleshooting](#troubleshooting)
- [Safety Features](#safety-features)

## Overview

The File Operations Utility is a Python script designed to facilitate batch operations on files and directories. It provides a safe, flexible, and powerful way to:

- Delete files with specific extensions
- Copy files matching certain criteria
- Move files from one location to another
- Handle directories as well as files
- Execute operations with various matching strategies
- Process files and directories based on patterns in a text file (similar to .gitignore)
- Perform operations with safety features (confirmation, backup, dry run)

The utility is specifically designed to handle complex file management scenarios, including:
- Operations on files with multiple extensions (e.g., file.tar.gz)
- Exclusion-based operations (e.g., delete all files EXCEPT certain ones)
- Directory-specific operations
- Recursive and non-recursive searches
- Pattern-based file selection using a patterns file

## Installation

### Prerequisites
- Python 3.6 or higher

### Setup
1. Save the script as `file_ops.py` in your desired location
2. Make the script executable (Linux/Mac):
   ```bash
   chmod +x file_ops.py
   ```
3. (Optional) Add the script to your PATH for system-wide access

No additional Python packages are required as the script only uses standard library modules.

## Basic Usage

The basic syntax of the command is:

```bash
python file_ops.py OPERATION [OPTIONS]
```

Where `OPERATION` is one of:
- `delete`: Remove files matching the criteria
- `copy`: Copy files matching the criteria to a destination
- `move`: Move files matching the criteria to a destination

### Simple Examples

```bash
# Delete all .tmp files in the current directory
python file_ops.py delete --extensions tmp

# Copy all PDF files to a backup directory
python file_ops.py copy --extensions pdf --dest_dir /path/to/backup

# Move all image files to an archive folder
python file_ops.py move --extensions jpg png gif --dest_dir /path/to/images

# Use a patterns file to define which files to delete
python file_ops.py delete --patterns-file cleanup.txt
```

## Command-line Arguments

### Required Arguments

- `operation`: One of `delete`, `copy`, or `move`. Specifies the operation to perform.

### Source Options

- `--source_dir SOURCE_DIR`: Source directory path (default: current directory '.')

### Target Options

- `--extensions EXT1 [EXT2 ...]`: File extensions to target (e.g., jpg png txt)
- `--contains-extension`: Match files containing the extension anywhere (e.g., file.msg.1 matches with --extensions msg)
- `--exact-match FILE1 [FILE2 ...]`: Match files with exact filenames specified
- `--include-dirs`: Include directories in the operations
- `--target_dirs DIR1 [DIR2 ...]`: Directory names to target when --include-dirs is enabled

### Pattern File Options

- `--patterns-file FILE`: Path to a file containing patterns to match (similar to .gitignore format)
- `--patterns-exclude`: Treat all patterns from the file as exclusions (both files and directories)
- `--patterns-excludeFiles`: Treat only file patterns from the file as exclusions (keeps directories)
- `--patterns-excludeDirs`: Treat only directory patterns from the file as exclusions (keeps files)
- `--patterns-override`: Patterns from file override (rather than supplement) command-line patterns

### Exclusion Options

- `--exclude-extensions EXT1 [EXT2 ...]`: File extensions to exclude
- `--exclude-exact FILE1 [FILE2 ...]`: Exclude files with exact filenames specified
- `--exclude-contains STR1 [STR2 ...]`: Exclude files containing specified strings
- `--exclude-all-but`: Exclude all files EXCEPT those matching the target criteria

### Behavior Options

- `--dest_dir DEST_DIR`: Destination directory (required for copy/move operations)
- `--no-recursive`: Do not search subdirectories (default: search recursively)

### Safety Options

- `--no-confirm`: Skip confirmation prompt
- `--dry-run`: Show what would be done without actually doing it
- `--backup`: Create a backup of the source directory before making changes

### Output Options

- `--verbose`: Show detailed information about each processed item
- `--quiet`: Suppress all non-error output

## Use Cases

### Basic File Operations

#### Delete temporary files
```bash
python file_ops.py delete --extensions tmp bak
```

#### Copy all documents to a backup folder
```bash
python file_ops.py copy --extensions doc docx pdf txt --dest_dir /path/to/backup
```

#### Move images to an archive
```bash
python file_ops.py move --extensions jpg jpeg png gif --dest_dir /path/to/images
```

### Working with Multiple Extensions

#### Delete both Python and text files
```bash
python file_ops.py delete --extensions py txt
```

#### Copy all source code files
```bash
python file_ops.py copy --extensions py js html css php --dest_dir /path/to/code_backup
```

### Using Pattern Files

#### Use a patterns file to define files to delete
```bash
python file_ops.py delete --patterns-file cleanup.txt
```
This will delete files and directories that match the patterns in `cleanup.txt`.

#### Use a patterns file to define files to exclude (keep)
```bash
python file_ops.py delete --patterns-file important.txt --patterns-exclude
```
This will delete all files and directories EXCEPT those matching the patterns in `important.txt`.

#### Use a patterns file to exclude only files, but include directories
```bash
python file_ops.py delete --patterns-file mixed.txt --patterns-excludeFiles
```
This will exclude files matching the patterns in `mixed.txt`, but will process any directories listed in the file.

#### Use a patterns file to exclude only directories, but include files
```bash
python file_ops.py delete --patterns-file mixed.txt --patterns-excludeDirs
```
This will exclude directories matching the patterns in `mixed.txt`, but will process any files listed in the file and all other files.

#### Let patterns file override command-line options
```bash
python file_ops.py delete --extensions txt --patterns-file cleanup.txt --patterns-override
```
By default, patterns in the file supplement command-line arguments. With `--patterns-override`, the patterns in the file take precedence.

### Non-recursive Operations

#### Delete log files only in the top-level directory
```bash
python file_ops.py delete --extensions log --no-recursive
```

#### Copy only main configuration files (not in subdirectories)
```bash
python file_ops.py copy --extensions conf ini --no-recursive --dest_dir /path/to/config_backup
```

### Handling Special Filenames

#### Delete files with compound extensions
```bash
python file_ops.py delete --extensions tar.gz --contains-extension
```
This will match files like `backup.tar.gz`, `data.tar.gz`, etc.

#### Delete specific files by name
```bash
python file_ops.py delete --exact-match config.bak old_data.tmp unwanted.log
```

#### Delete files with incremental numbering
```bash
python file_ops.py delete --extensions log --contains-extension
```
This will match `server.log`, `server.log.1`, `server.log.2`, etc.

### Exclusion Operations

#### Delete all files EXCEPT documents (Method 1)
```bash
python file_ops.py delete --extensions doc docx pdf txt --exclude-all-but
```

#### Delete all files EXCEPT documents (Method 2)
```bash
python file_ops.py delete --exclude-extensions doc docx pdf txt
```

#### Copy all files except backups and temps
```bash
python file_ops.py copy --dest_dir /path/to/clean_backup --exclude-extensions bak tmp old
```

#### Delete all files except those containing "important" in the name
```bash
python file_ops.py delete --exclude-contains important
```

#### Complex exclusion: Keep code and docs, delete everything else
```bash
python file_ops.py delete --extensions py js html md txt pdf --exclude-all-but
```

### Directory Operations

#### Move specific directories
```bash
python file_ops.py move --include-dirs --target_dirs logs temp cache --dest_dir /path/to/archive
```

#### Copy image files and their thumbnail directories
```bash
python file_ops.py copy --extensions jpg png --include-dirs --target_dirs thumbnails --dest_dir /path/to/media_backup
```

### Preview Mode

#### Preview which files would be deleted
```bash
python file_ops.py delete --extensions log tmp --dry-run
```

#### Preview a complex operation before executing
```bash
python file_ops.py move --source_dir /path/to/project --extensions py js --exclude-contains test debug --dest_dir /path/to/clean_project --dry-run
```

#### Preview pattern-based operations
```bash
python file_ops.py delete --patterns-file cleanup.txt --dry-run
```

### Backup Before Operations

#### Delete with safety backup
```bash
python file_ops.py delete --extensions log --backup
```
This creates a timestamped backup of the source directory before performing the delete operation.

## Pattern File Format

The pattern file uses a simple, intuitive format similar to `.gitignore`:

```
# Comments start with a hash character

# File extensions (start with a dot)
.jpg
.tmp
.bak

# Directories (end with a slash)
logs/
cache/
__pycache__/

# Exact filenames (without special prefix/suffix)
config.ini
data.log
temp.xml

# Contains patterns (start with an asterisk)
*backup
*temp
*old
```

Each line in the pattern file is categorized based on its format:
- **Extensions**: Lines starting with `.` (e.g., `.jpg`, `.tmp`) match file extensions
- **Directories**: Lines ending with `/` (e.g., `logs/`, `cache/`) match directory names
- **Contains patterns**: Lines starting with `*` (e.g., `*backup`) match if the string appears anywhere in the filename
- **Exact filenames**: All other lines match exact filenames

The pattern file can be used in different ways:
- With no flags: Include all patterns in the file
- With `--patterns-exclude`: Exclude all patterns in the file
- With `--patterns-excludeFiles`: Exclude only file patterns, include directory patterns
- With `--patterns-excludeDirs`: Exclude only directory patterns, include file patterns

## Advanced Examples

### Clean a development directory
```bash
python file_ops.py delete --extensions pyc pyo pyd --include-dirs --target_dirs __pycache__ .pytest_cache
```

### Using a pattern file for project cleanup
```bash
# Pattern file (cleanup.txt) contents:
# .pyc
# .pyo
# .pyd
# __pycache__/
# .pytest_cache/

python file_ops.py delete --patterns-file cleanup.txt
```

### Organize files by extension
```bash
# Move all images to an images folder
python file_ops.py move --extensions jpg jpeg png gif --dest_dir ./images

# Move all documents to a docs folder
python file_ops.py move --extensions doc docx pdf txt --dest_dir ./documents

# Move all audio files to a music folder
python file_ops.py move --extensions mp3 wav flac --dest_dir ./music
```

### Complex filtering with pattern files and exclusions
```bash
# Pattern file (important.txt) contents:
# .py
# .md
# docs/
# tests/

# Keep important code and documentation, delete everything else
python file_ops.py delete --patterns-file important.txt --patterns-exclude

# Delete code files but keep their directories
python file_ops.py delete --patterns-file important.txt --patterns-excludeDirs
```

### Backup only important files using patterns
```bash
# Pattern file (backup.txt) contents:
# .py
# .js
# .html
# .css
# .md
# .txt
# images/
# docs/

python file_ops.py copy --patterns-file backup.txt --dest_dir /backup
```

### Incrementally delete temporary files by type
```bash
# Pattern file (temps.txt) contents:
# .tmp
# .bak
# .cache
# .log
# cache/
# logs/

# First preview what would be deleted
python file_ops.py delete --patterns-file temps.txt --dry-run

# Then delete only temp files but keep the log directories
python file_ops.py delete --patterns-file temps.txt --patterns-excludeDirs
```

## Troubleshooting

### No files found
- Check that you're in the correct directory or that `--source_dir` points to the right location
- Verify file extensions (they are case-insensitive but must otherwise match exactly)
- If using `--contains-extension`, make sure the extension is part of the filename
- Check if `--no-recursive` is limiting your search

### Pattern file issues
- Ensure the pattern file exists and is readable
- Verify pattern format (extensions start with `.`, directories end with `/`, etc.)
- Check for typos in pattern entries
- Use `--dry-run` to preview which files/directories would be matched
- If directories aren't being included/excluded properly, check if you're using the right flag (`--patterns-exclude` vs `--patterns-excludeFiles` vs `--patterns-excludeDirs`)

### Operation targeting wrong files
- Use `--dry-run` to preview which files will be affected
- Check your extension specifications (e.g., `.txt` vs `txt`)
- When using exclusions, verify the logic is what you expect
- Remember that `--patterns-exclude` excludes both files and directories
- Use `--patterns-excludeFiles` to exclude only files
- Use `--patterns-excludeDirs` to exclude only directories

### Script fails to start
- Ensure you have Python 3.6 or higher installed
- Check file permissions (the script should be executable)
- Make sure the script path is correct

## Safety Features

This utility includes several safety features to prevent accidental data loss:

1. **Confirmation prompts**: By default, the script asks for confirmation before executing operations
2. **Dry run mode**: Use `--dry-run` to see what would happen without making changes
3. **Backup functionality**: Create automatic backups before operations with `--backup`
4. **Destination directory checks**: The script verifies destination directories exist or offers to create them
5. **Detailed logging**: See exactly what's happening with `--verbose`
6. **Pattern file validation**: The script validates pattern files and reports errors clearly

Remember to use `--dry-run` first when working with critical data or when using complex matching criteria, especially when using pattern files for the first time.