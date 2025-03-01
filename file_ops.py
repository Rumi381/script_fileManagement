#!/usr/bin/env python3
"""
File Operations Utility

A versatile command-line tool for finding and performing operations (delete, copy, move)
on files and directories based on extensions or directory names.
"""

import os
import sys
import shutil
import argparse
from datetime import datetime
import logging


def setup_logging(verbose):
    """Configure logging based on verbosity level."""
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(message)s'
    )
    return logging.getLogger('file_ops')


def parse_patterns_file(file_path, logger=None):
    """
    Parse a patterns file into categories of patterns.
    
    Format:
        # Comment
        .jpg                # Extension (starts with .)
        logs/               # Directory (ends with /)
        config.ini          # Exact filename
        *backup             # Contains pattern (starts with *)
        
    Returns:
        dict: Dictionary with keys 'extensions', 'directories', 'exact', 'contains'
              and corresponding lists of patterns
    """
    if not os.path.exists(file_path):
        if logger:
            logger.error(f"Patterns file not found: {file_path}")
        return None
        
    patterns = {
        'extensions': [],
        'directories': [],
        'exact': [],
        'contains': []
    }
    
    try:
        with open(file_path, 'r') as f:
            for line in f:
                # Remove comments and whitespace
                line = line.split('#', 1)[0].strip()
                
                if not line:
                    continue
                    
                # Categorize the pattern
                if line.startswith('.'):
                    # Extension pattern (e.g., .jpg)
                    ext = line.lower()
                    patterns['extensions'].append(ext)
                elif line.endswith('/'):
                    # Directory pattern (e.g., logs/)
                    dir_name = line[:-1]  # Remove trailing slash
                    patterns['directories'].append(dir_name)
                elif line.startswith('*'):
                    # Contains pattern (e.g., *backup)
                    pattern = line[1:]  # Remove leading asterisk
                    patterns['contains'].append(pattern)
                else:
                    # Exact filename pattern (e.g., config.ini)
                    patterns['exact'].append(line)
                    
        return patterns
    except Exception as e:
        if logger:
            logger.error(f"Error parsing patterns file: {e}")
        return None


def find_matching_items(source_dir, extensions=None, include_dirs=False, 
                        target_dirs=None, recursive=True, 
                        contains_extension=False, exact_match=None,
                        exclude_extensions=None, exclude_exact=None, exclude_contains=None,
                        exclude_dirs=None, exclude_all_but=False, include_all_files=False,
                        include_all_dirs=False, logger=None):
    """
    Find files with matching extensions and/or directories with matching names.
    
    Args:
        source_dir (str): Directory to search in
        extensions (list): List of file extensions to match (with dots)
        include_dirs (bool): Whether to include directories in results
        target_dirs (list): List of directory names to match
        recursive (bool): Whether to search recursively
        contains_extension (bool): If True, match files containing the extension anywhere
        exact_match (list): Match files with exact filenames specified
        exclude_extensions (list): List of extensions to exclude (with dots)
        exclude_exact (list): List of exact filenames to exclude
        exclude_contains (list): List of strings to exclude files containing these
        exclude_dirs (list): List of directory names to exclude
        exclude_all_but (bool): If True, exclude all files except those matching criteria
        include_all_files (bool): If True, include all files that aren't explicitly excluded
        include_all_dirs (bool): If True, include all directories except those explicitly excluded
        logger: Logger object
        
    Returns:
        tuple: (matched_files, matched_dirs)
    """
    matched_files = []
    matched_dirs = []
    
    # Check for valid criteria
    has_inclusion_criteria = extensions or exact_match or include_all_files or (include_dirs and target_dirs)
    has_exclusion_criteria = exclude_extensions or exclude_exact or exclude_contains or exclude_dirs
    
    # Only validate if we don't have exclusion criteria
    if not has_inclusion_criteria and not has_exclusion_criteria and not exclude_all_but:
        if logger:
            logger.error("Error: You must specify either file extensions, target directories, or exact filenames")
        return [], []
    
    # Validation for exclude-all-but mode
    if exclude_all_but and not has_inclusion_criteria:
        if logger:
            logger.error("Error: When using --exclude-all-but, you must specify which files to keep with --extensions or --exact-match")
        return [], []
        
    # Normalize extensions (ensure they start with a dot)
    if extensions:
        extensions = [ext.lower() if ext.startswith('.') else '.' + ext.lower() for ext in extensions]
    
    # Normalize exclude extensions
    if exclude_extensions:
        exclude_extensions = [ext.lower() if ext.startswith('.') else '.' + ext.lower() for ext in exclude_extensions]
    
    def file_matches_criteria(filename):
        """Check if file matches the main search criteria (extensions, exact_match) or if include_all_files is True"""
        if include_all_files:
            return True
            
        if exact_match and filename in exact_match:
            return True
        
        if extensions:
            # Standard extension matching
            file_ext = os.path.splitext(filename)[1].lower()
            if file_ext in extensions:
                return True
                
            # Extended matching for files like "file.msg.1"
            if contains_extension:
                filename_lower = filename.lower()
                for ext in extensions:
                    if ext in filename_lower:
                        return True
        
        return False
    
    def file_matches_exclusion(filename):
        """Check if file matches any exclusion criteria"""
        if exclude_exact and filename in exclude_exact:
            return True
            
        if exclude_extensions:
            file_ext = os.path.splitext(filename)[1].lower()
            if file_ext in exclude_extensions:
                return True
                
        if exclude_contains:
            filename_lower = filename.lower()
            for pattern in exclude_contains:
                if pattern.lower() in filename_lower:
                    return True
        
        return False
    
    if recursive:
        # Recursive search through all subdirectories
        for root, dirs, files in os.walk(source_dir):
            # Process files
            for file in files:
                matches_criteria = file_matches_criteria(file)
                matches_exclusion = file_matches_exclusion(file)
                
                # Determine if file should be included in the results based on mode
                if exclude_all_but:
                    # In exclude-all-but mode, we process files that DON'T match our keep criteria
                    # and aren't explicitly excluded
                    if not matches_criteria and not matches_exclusion:
                        matched_files.append(os.path.join(root, file))
                else:
                    # In normal mode, process files that match criteria AND aren't excluded
                    # If no explicit criteria specified, match all files that aren't excluded
                    if (matches_criteria or not (extensions or exact_match) or include_all_files) and not matches_exclusion:
                        matched_files.append(os.path.join(root, file))
            
            # Process directories
            for dir_name in dirs:
                # Skip excluded directories
                if exclude_dirs and dir_name in exclude_dirs:
                    continue
                    
                # Include directory if:
                # 1. include_all_dirs is True (include all non-excluded directories), OR
                # 2. include_dirs is True AND directory name is in target_dirs
                if include_all_dirs or (include_dirs and target_dirs and dir_name in target_dirs):
                    dir_path = os.path.join(root, dir_name)
                    matched_dirs.append(dir_path)
    else:
        # Non-recursive search, only in the source directory
        for item in os.listdir(source_dir):
            item_path = os.path.join(source_dir, item)
            
            # Process files
            if os.path.isfile(item_path):
                matches_criteria = file_matches_criteria(item)
                matches_exclusion = file_matches_exclusion(item)
                
                # Determine if file should be included in the results based on mode
                if exclude_all_but:
                    # In exclude-all-but mode, we process files that DON'T match our keep criteria
                    # and aren't explicitly excluded
                    if not matches_criteria and not matches_exclusion:
                        matched_files.append(item_path)
                else:
                    # In normal mode, process files that match criteria AND aren't excluded
                    # If no explicit criteria specified, match all files that aren't excluded
                    if (matches_criteria or not (extensions or exact_match) or include_all_files) and not matches_exclusion:
                        matched_files.append(item_path)
            
            # Process directories
            elif os.path.isdir(item_path):
                dir_name = os.path.basename(item_path)
                # Skip excluded directories
                if exclude_dirs and dir_name in exclude_dirs:
                    continue
                
                # Include directory if:
                # 1. include_all_dirs is True (include all non-excluded directories), OR
                # 2. include_dirs is True AND directory name is in target_dirs
                if include_all_dirs or (include_dirs and target_dirs and dir_name in target_dirs):
                    matched_dirs.append(item_path)
    
    return matched_files, matched_dirs


def process_items(operation, items, source_dir, dest_dir=None, 
                 is_dirs=False, dry_run=False, logger=None):
    """
    Process matched items according to the specified operation.
    
    Args:
        operation (str): Operation to perform ('delete', 'copy', 'move')
        items (list): List of file or directory paths to process
        source_dir (str): Source directory path
        dest_dir (str): Destination directory path (for copy/move)
        is_dirs (bool): Whether the items are directories
        dry_run (bool): If True, don't actually perform operations
        logger: Logger object
        
    Returns:
        tuple: (processed_count, errors)
    """
    processed_count = 0
    errors = []
    
    for item_path in items:
        try:
            rel_path = os.path.relpath(item_path, source_dir)
            
            if dry_run:
                if operation == 'delete':
                    logger.info(f"Would delete: {item_path}")
                else:
                    dest_item_path = os.path.join(dest_dir, rel_path)
                    logger.info(f"Would {operation}: {item_path} -> {dest_item_path}")
                processed_count += 1
                continue
                
            if operation == 'delete':
                if is_dirs:
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
                logger.debug(f"Deleted: {item_path}")
                
            elif operation == 'copy':
                dest_item_path = os.path.join(dest_dir, rel_path)
                dest_parent_dir = os.path.dirname(dest_item_path)
                
                if not os.path.exists(dest_parent_dir):
                    os.makedirs(dest_parent_dir)
                    
                if is_dirs:
                    shutil.copytree(item_path, dest_item_path)
                else:
                    shutil.copy2(item_path, dest_item_path)
                logger.debug(f"Copied: {item_path} -> {dest_item_path}")
                
            elif operation == 'move':
                dest_item_path = os.path.join(dest_dir, rel_path)
                dest_parent_dir = os.path.dirname(dest_item_path)
                
                if not os.path.exists(dest_parent_dir):
                    os.makedirs(dest_parent_dir)
                    
                shutil.move(item_path, dest_item_path)
                logger.debug(f"Moved: {item_path} -> {dest_item_path}")
            
            processed_count += 1
            
        except Exception as e:
            errors.append((item_path, str(e)))
            logger.debug(f"Error processing {item_path}: {e}")
    
    return processed_count, errors


def create_backup(source_dir, dest_dir, logger=None):
    """Create a backup of the source directory before making changes."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"{source_dir}_backup_{timestamp}"
    try:
        shutil.copytree(source_dir, backup_dir)
        if logger:
            logger.info(f"Created backup at: {backup_dir}")
        return True
    except Exception as e:
        if logger:
            logger.error(f"Backup failed: {e}")
        return False


def main():
    # Create argument parser with detailed help information
    parser = argparse.ArgumentParser(
        description="""
File Operations Utility: Find and perform operations on files and directories based on 
extensions or directory names.

This script allows you to delete, copy, or move files with specific extensions and/or
directories with specific names. It provides options for recursive searching, 
creating backups, and previewing operations before executing them.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Delete all .tmp files in current directory
  python file_ops.py delete --extensions tmp
  
  # Copy all PDF and DOCX files from current directory to another location
  python file_ops.py copy --dest_dir /path/to/destination --extensions pdf docx
  
  # Delete all files containing .msg, including .msg.1, .msg.2, etc.
  python file_ops.py delete --extensions msg --contains-extension
  
  # Delete specific files by exact name
  python file_ops.py delete --exact-match config.ini data.log
  
  # Delete all files EXCEPT .txt and .md files (keep only text files)
  python file_ops.py delete --extensions txt md --exclude-all-but
  
  # Delete all files EXCEPT those with specified extensions (alternative method)
  python file_ops.py delete --exclude-extensions tmp bak log
  
  # Copy all files except those containing "backup" in the filename
  python file_ops.py copy --dest_dir /path/to/destination --exclude-contains backup
  
  # Use a patterns file to specify which files to delete
  python file_ops.py delete --patterns-file cleanup_patterns.txt
  
  # Use a patterns file for exclusions (files to keep)
  python file_ops.py delete --patterns-file important_files.txt --patterns-exclude
  
  # Use a patterns file but exclude only the file patterns (keep directories)
  python file_ops.py delete --patterns-file mixed_patterns.txt --patterns-excludeFiles
  
  # Use a patterns file but exclude only the directory patterns (keep files)
  python file_ops.py delete --patterns-file mixed_patterns.txt --patterns-excludeDirs
  
  # Move both JPG files and directories named "thumbnails" from a source to destination
  python file_ops.py move --source_dir /path/to/source --dest_dir /path/to/destination --extensions jpg --include-dirs --target_dirs thumbnails
  
  # Preview what would be deleted without actually deleting (dry run)
  python file_ops.py delete --source_dir /path/to/source --extensions log tmp --dry-run
  
  # Only search in the specified directory, not in subdirectories
  python file_ops.py delete --source_dir /path/to/source --extensions bak --no-recursive
  
  # Create a backup before deleting files
  python file_ops.py delete --source_dir /path/to/source --extensions tmp --backup
        """
    )
    
    # Create argument groups for better organization
    required_group = parser.add_argument_group('Required Arguments')
    source_group = parser.add_argument_group('Source Options')
    target_group = parser.add_argument_group('Target Options')
    pattern_group = parser.add_argument_group('Pattern File Options')
    exclusion_group = parser.add_argument_group('Exclusion Options')
    behavior_group = parser.add_argument_group('Behavior Options')
    safety_group = parser.add_argument_group('Safety Options')
    output_group = parser.add_argument_group('Output Options')
    
    # Required arguments
    required_group.add_argument(
        'operation',
        choices=['delete', 'copy', 'move'],
        help='Operation to perform on the matched items'
    )
    
    # Source options
    source_group.add_argument(
        '--source_dir', 
        default='.',
        help='Source directory path (default: current directory)'
    )
    
    # Target options
    target_group.add_argument(
        '--extensions',
        nargs='+',
        help='File extensions to target (e.g., jpg png txt)'
    )
    target_group.add_argument(
        '--contains-extension',
        action='store_true',
        help='Match files containing the extension anywhere (e.g., file.msg.1 matches with --extensions msg)'
    )
    target_group.add_argument(
        '--exact-match',
        nargs='+',
        help='Match files with exact filenames specified (including extension)'
    )
    target_group.add_argument(
        '--include-dirs',
        action='store_true',
        help='Include directories in the operations'
    )
    target_group.add_argument(
        '--target_dirs',
        nargs='+',
        help='Directory names to target when --include-dirs is enabled'
    )
    
    # Pattern File Options
    pattern_group.add_argument(
        '--patterns-file',
        help='Path to a file containing patterns to match (similar to .gitignore format)'
    )
    pattern_group.add_argument(
        '--patterns-exclude',
        action='store_true',
        help='Treat all patterns from the file as exclusions (both files and directories)'
    )
    pattern_group.add_argument(
        '--patterns-excludeFiles',
        action='store_true',
        help='Treat only file patterns from the file as exclusions (keeps directories)'
    )
    pattern_group.add_argument(
        '--patterns-excludeDirs',
        action='store_true',
        help='Treat only directory patterns from the file as exclusions (keeps files)'
    )
    pattern_group.add_argument(
        '--patterns-override',
        action='store_true',
        help='Patterns from file override (rather than supplement) command-line patterns'
    )
    
    # Exclusion options
    exclusion_group.add_argument(
        '--exclude-extensions',
        nargs='+',
        help='File extensions to exclude (e.g., bak tmp)'
    )
    exclusion_group.add_argument(
        '--exclude-exact',
        nargs='+',
        help='Exclude files with exact filenames specified'
    )
    exclusion_group.add_argument(
        '--exclude-contains',
        nargs='+',
        help='Exclude files containing specified strings'
    )
    exclusion_group.add_argument(
        '--exclude-all-but',
        action='store_true',
        help='Exclude all files EXCEPT those matching the target criteria'
    )
    
    # Behavior options
    behavior_group.add_argument(
        '--dest_dir',
        help='Destination directory (required for copy/move operations)'
    )
    behavior_group.add_argument(
        '--no-recursive',
        action='store_true',
        help='Do not search subdirectories (default: search recursively)'
    )
    
    # Safety options
    safety_group.add_argument(
        '--no-confirm',
        action='store_true',
        help='Skip confirmation prompt'
    )
    safety_group.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without actually doing it'
    )
    safety_group.add_argument(
        '--backup',
        action='store_true',
        help='Create a backup of the source directory before making changes'
    )
    
    # Output options
    output_group.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed information about each processed item'
    )
    output_group.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress all non-error output'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(args.verbose)
    if args.quiet and not args.verbose:
        logger.setLevel(logging.ERROR)
    
    # Validate required arguments based on operation
    if args.operation in ['copy', 'move'] and not args.dest_dir:
        parser.error(f"The {args.operation} operation requires a destination directory (--dest_dir)")
    
    # Validate pattern exclusion flags - only one can be used at a time
    pattern_exclusion_flags = sum([
        1 if args.patterns_exclude else 0,
        1 if args.patterns_excludeFiles else 0,
        1 if args.patterns_excludeDirs else 0
    ])
    
    if pattern_exclusion_flags > 1:
        parser.error("Only one of --patterns-exclude, --patterns-excludeFiles, or --patterns-excludeDirs can be used at a time")
    
    # Initialize processing variables
    exclude_dirs = None
    include_all_files = False
    
    # Validate target options
    has_inclusion_criteria = args.extensions or args.exact_match or (args.include_dirs and args.target_dirs)
    has_exclusion_criteria = args.exclude_extensions or args.exclude_exact or args.exclude_contains
    
    # Process patterns file if specified
    file_patterns = None
    if args.patterns_file:
        file_patterns = parse_patterns_file(args.patterns_file, logger)
        if file_patterns is None:
            return 1
        
        # Process file patterns differently based on the exclusion mode
        if args.patterns_exclude:
            # Exclude all patterns (files and directories)
            # But include all other files and directories not explicitly excluded
            include_all_files = True  # Include all files not explicitly excluded
            include_all_dirs = True   # Include all directories not explicitly excluded
            has_inclusion_criteria = True
            
            if file_patterns.get('extensions'):
                args.exclude_extensions = file_patterns['extensions'] + (args.exclude_extensions or [])
                
            if file_patterns.get('exact'):
                args.exclude_exact = file_patterns['exact'] + (args.exclude_exact or [])
                
            if file_patterns.get('contains'):
                args.exclude_contains = file_patterns['contains'] + (args.exclude_contains or [])
                
            if file_patterns.get('directories'):
                exclude_dirs = file_patterns['directories']
                
        elif args.patterns_excludeFiles:
            # Exclude file patterns, include directory patterns
            if file_patterns.get('extensions'):
                args.exclude_extensions = file_patterns['extensions'] + (args.exclude_extensions or [])
                has_exclusion_criteria = True
                
            if file_patterns.get('exact'):
                args.exclude_exact = file_patterns['exact'] + (args.exclude_exact or [])
                has_exclusion_criteria = True
                
            if file_patterns.get('contains'):
                args.exclude_contains = file_patterns['contains'] + (args.exclude_contains or [])
                has_exclusion_criteria = True
                
            # Include directories if there are any in the patterns file
            if file_patterns.get('directories'):
                args.include_dirs = True
                args.target_dirs = file_patterns['directories'] + (args.target_dirs or [])
                has_inclusion_criteria = True
                
        elif args.patterns_excludeDirs:
            # Exclude directory patterns, include file patterns and all other files
            include_all_files = True
            include_all_dirs = True  # Include all directories except those excluded
            has_inclusion_criteria = True
            
            if file_patterns.get('extensions'):
                args.extensions = file_patterns['extensions'] + (args.extensions or [])
                
            if file_patterns.get('exact'):
                args.exact_match = file_patterns['exact'] + (args.exact_match or [])
                
            if file_patterns.get('directories'):
                exclude_dirs = file_patterns['directories']
        
        else:
            # Normal inclusion mode - include all patterns
            if file_patterns.get('extensions') and (args.patterns_override or not args.extensions):
                args.extensions = file_patterns['extensions'] + ([] if args.patterns_override else (args.extensions or []))
                has_inclusion_criteria = True
                
            if file_patterns.get('exact') and (args.patterns_override or not args.exact_match):
                args.exact_match = file_patterns['exact'] + ([] if args.patterns_override else (args.exact_match or []))
                has_inclusion_criteria = True
                
            if file_patterns.get('contains'):
                # Contains patterns are treated as exclusion by default
                args.exclude_contains = file_patterns['contains'] + (args.exclude_contains or [])
                has_exclusion_criteria = True
                
            if file_patterns.get('directories'):
                args.include_dirs = True
                args.target_dirs = file_patterns['directories'] + ([] if args.patterns_override else (args.target_dirs or []))
                has_inclusion_criteria = True
    
    # For normal mode, we need either inclusion OR exclusion criteria
    # When using patterns-excludeDirs, we're implicitly including all files
    if not include_all_files and not args.exclude_all_but and not has_inclusion_criteria and not has_exclusion_criteria:
        parser.error("You must specify either inclusion criteria (--extensions, --exact-match, --target_dirs) "
                      "or exclusion criteria (--exclude-extensions, --exclude-exact, --exclude-contains) "
                      "or use a patterns file (--patterns-file)")
    
    # For exclude-all-but mode, we need inclusion criteria
    if args.exclude_all_but and not has_inclusion_criteria:
        parser.error("When using --exclude-all-but, you must specify which files to keep with --extensions or --exact-match")
    
    if args.include_dirs and not args.target_dirs:
        parser.error("When --include-dirs is specified, you must provide directory names with --target_dirs")
        
    if args.contains_extension and not args.extensions:
        parser.error("The --contains-extension option requires --extensions to be specified")
    
    # Validate source directory
    if not os.path.isdir(args.source_dir):
        logger.error(f"Error: Source directory '{args.source_dir}' does not exist.")
        return 1
    
    # Validate destination directory for copy/move operations
    if args.dest_dir and not os.path.exists(args.dest_dir) and not args.dry_run:
        create_dest = input(f"Destination directory '{args.dest_dir}' doesn't exist. Create it? (y/n): ")
        if create_dest.lower() == 'y':
            try:
                os.makedirs(args.dest_dir)
                logger.info(f"Created destination directory: {args.dest_dir}")
            except Exception as e:
                logger.error(f"Error creating destination directory: {e}")
                return 1
        else:
            logger.info("Operation cancelled.")
            return 1
    
    # Create backup if requested
    if args.backup and not args.dry_run:
        logger.info("Creating backup...")
        if not create_backup(args.source_dir, args.dest_dir, logger):
            confirm = input("Backup failed. Continue anyway? (y/n): ")
            if confirm.lower() != 'y':
                logger.info("Operation cancelled.")
                return 1
    
    # Find matching files and directories
    recursive = not args.no_recursive
    matched_files, matched_dirs = find_matching_items(
        args.source_dir, 
        extensions=args.extensions,
        include_dirs=args.include_dirs,
        target_dirs=args.target_dirs,
        recursive=recursive,
        contains_extension=args.contains_extension,
        exact_match=args.exact_match,
        exclude_extensions=args.exclude_extensions,
        exclude_exact=args.exclude_exact,
        exclude_contains=args.exclude_contains,
        exclude_dirs=exclude_dirs,
        exclude_all_but=args.exclude_all_but,
        include_all_files=include_all_files,
        include_all_dirs=include_all_dirs if 'include_all_dirs' in locals() else False,
        logger=logger
    )
    
    total_matched = len(matched_files) + len(matched_dirs)
    
    if total_matched == 0:
        if args.exclude_all_but:
            logger.info("No files found that don't match your criteria. Everything will be kept.")
        else:
            extensions_msg = f" with extensions {', '.join(args.extensions)}" if args.extensions else ""
            dirs_msg = f" or directories named {', '.join(args.target_dirs) if args.target_dirs else []}"
            logger.info(f"No files{extensions_msg}{dirs_msg} found in {args.source_dir}")
        return 0
    
    # Show summary and get confirmation
    if args.exclude_all_but:
        logger.info(f"\nFound {total_matched} items that DON'T match your criteria (will be processed):")
    else:
        logger.info(f"\nFound {total_matched} items to process:")
    
    if len(matched_files) > 0:
        logger.info(f" - {len(matched_files)} files")
        sample_files = matched_files[:3] if not args.verbose else matched_files
        for file in sample_files:
            logger.info(f"   * {file}")
        if not args.verbose and len(matched_files) > 3:
            logger.info(f"   * ... and {len(matched_files) - 3} more files")
    
    if len(matched_dirs) > 0:
        logger.info(f" - {len(matched_dirs)} directories")
        sample_dirs = matched_dirs[:3] if not args.verbose else matched_dirs
        for dir_path in sample_dirs:
            logger.info(f"   * {dir_path}")
        if not args.verbose and len(matched_dirs) > 3:
            logger.info(f"   * ... and {len(matched_dirs) - 3} more directories")
    
    if args.dry_run:
        logger.info("\nDRY RUN: No items will be modified.")
    elif not args.no_confirm:
        confirm = input(f"\nAre you sure you want to {args.operation} these items? (y/n): ")
        if confirm.lower() != 'y':
            logger.info("Operation cancelled.")
            return 0
    
    # Process files and directories
    logger.info(f"\nPerforming {args.operation} operation...")
    
    files_processed, file_errors = process_items(
        args.operation,
        matched_files,
        args.source_dir,
        args.dest_dir,
        is_dirs=False,
        dry_run=args.dry_run,
        logger=logger
    )
    
    dirs_processed, dir_errors = process_items(
        args.operation,
        matched_dirs,
        args.source_dir,
        args.dest_dir,
        is_dirs=True,
        dry_run=args.dry_run,
        logger=logger
    )
    
    total_processed = files_processed + dirs_processed
    all_errors = file_errors + dir_errors
    
    # Show summary
    if not args.quiet:
        logger.info(f"\nOperation completed. {total_processed} items processed.")
        
        if all_errors:
            logger.error(f"\nErrors occurred for {len(all_errors)} items:")
            for item_path, error in all_errors[:5]:
                logger.error(f" - {item_path}: {error}")
            
            if len(all_errors) > 5:
                logger.error(f" - ... and {len(all_errors) - 5} more errors")
    
    return 0 if len(all_errors) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())