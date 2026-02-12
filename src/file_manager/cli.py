#!/usr/bin/env python3
"""
Command-line interface for automation features.
This provides batch operations without the TUI.
"""

import argparse
import sys
from pathlib import Path

try:
    from .automation import FileOrganizer
    from .search import FileSearcher
except ImportError:
    # Support running directly
    from automation import FileOrganizer
    from search import FileSearcher


def setup_parser():
    """Set up the argument parser."""
    parser = argparse.ArgumentParser(
        description="File Manager - Automation CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Organize files by type
  tfm-auto organize --source ~/Downloads --target ~/Organized --by-type
  
  # Organize files by date
  tfm-auto organize --source ~/Downloads --target ~/Organized --by-date
  
  # Search for files
  tfm-auto search --dir ~/Documents --name "*.pdf"
  
  # Find duplicate files
  tfm-auto duplicates --dir ~/Downloads
  
  # Cleanup old files
  tfm-auto cleanup --dir ~/Downloads --days 30 --dry-run
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Organize command
    organize_parser = subparsers.add_parser('organize', help='Organize files')
    organize_parser.add_argument('--source', required=True, help='Source directory')
    organize_parser.add_argument('--target', required=True, help='Target directory')
    organize_parser.add_argument('--by-type', action='store_true', help='Organize by file type')
    organize_parser.add_argument('--by-date', action='store_true', help='Organize by date')
    organize_parser.add_argument('--move', action='store_true', help='Move files instead of copy')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search for files')
    search_parser.add_argument('--dir', required=True, help='Directory to search')
    search_parser.add_argument('--name', help='File name pattern')
    search_parser.add_argument('--content', help='Search file contents')
    search_parser.add_argument('--case-sensitive', action='store_true', help='Case sensitive search')
    
    # Duplicates command
    dup_parser = subparsers.add_parser('duplicates', help='Find duplicate files')
    dup_parser.add_argument('--dir', required=True, help='Directory to search')
    dup_parser.add_argument('--recursive', action='store_true', default=True, help='Search recursively')
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Clean up old files')
    cleanup_parser.add_argument('--dir', required=True, help='Directory to clean')
    cleanup_parser.add_argument('--days', type=int, required=True, help='Delete files older than N days')
    cleanup_parser.add_argument('--dry-run', action='store_true', help='Show what would be deleted without deleting')
    cleanup_parser.add_argument('--recursive', action='store_true', help='Search recursively')
    
    # Rename command
    rename_parser = subparsers.add_parser('rename', help='Batch rename files')
    rename_parser.add_argument('--dir', required=True, help='Directory containing files')
    rename_parser.add_argument('--pattern', required=True, help='Text pattern to match')
    rename_parser.add_argument('--replacement', required=True, help='Replacement text')
    rename_parser.add_argument('--recursive', action='store_true', help='Process subdirectories')
    
    return parser


def handle_organize(args):
    """Handle the organize command."""
    organizer = FileOrganizer()
    source = Path(args.source)
    target = Path(args.target)

    if not source.exists():
        print(f"Error: Source directory does not exist: {source}")
        return 1

    if args.by_type:
        result = organizer.organize_by_type(source, target, move=args.move)
        print(f"Organized files by type:")
        for category, files in result.items():
            print(f"  {category}: {len(files)} files")
    elif args.by_date:
        result = organizer.organize_by_date(source, target, move=args.move)
        print(f"Organized files by date:")
        for date, files in result.items():
            print(f"  {date}: {len(files)} files")
    else:
        print("Error: Specify either --by-type or --by-date")
        return 1

    return 0


def handle_search(args):
    """Handle the search command."""
    searcher = FileSearcher()
    directory = Path(args.dir)

    if not directory.exists():
        print(f"Error: Directory does not exist: {directory}")
        return 1

    if args.name:
        results = searcher.search_by_name(
            directory,
            args.name,
            case_sensitive=args.case_sensitive
        )
        print(f"Found {len(results)} files matching '{args.name}':")
        for path in results:
            print(f"  {path}")
    elif args.content:
        results = searcher.search_by_content(
            directory,
            args.content,
            case_sensitive=args.case_sensitive
        )
        print(f"Found {len(results)} files containing '{args.content}':")
        for path in results:
            print(f"  {path}")
    else:
        print("Error: Specify either --name or --content")
        return 1

    return 0


def handle_duplicates(args):
    """Handle the duplicates command."""
    organizer = FileOrganizer()
    directory = Path(args.dir)

    if not directory.exists():
        print(f"Error: Directory does not exist: {directory}")
        return 1

    print(f"Searching for duplicates in {directory}...")
    duplicates = organizer.find_duplicates(directory, recursive=args.recursive)

    if duplicates:
        print(f"Found {len(duplicates)} groups of duplicate files:")
        for hash_val, files in duplicates.items():
            print(f"\n  Duplicate group ({len(files)} files):")
            for path in files:
                print(f"    {path}")
    else:
        print("No duplicates found.")

    return 0


def handle_cleanup(args):
    """Handle the cleanup command."""
    organizer = FileOrganizer()
    directory = Path(args.dir)

    if not directory.exists():
        print(f"Error: Directory does not exist: {directory}")
        return 1

    old_files = organizer.cleanup_old_files(
        directory,
        args.days,
        recursive=args.recursive,
        dry_run=args.dry_run
    )

    if args.dry_run:
        print(f"Would delete {len(old_files)} files older than {args.days} days:")
    else:
        print(f"Deleted {len(old_files)} files older than {args.days} days:")

    for path in old_files:
        print(f"  {path}")

    return 0


def handle_rename(args):
    """Handle the rename command."""
    organizer = FileOrganizer()
    directory = Path(args.dir)

    if not directory.exists():
        print(f"Error: Directory does not exist: {directory}")
        return 1

    renamed = organizer.batch_rename(
        directory,
        args.pattern,
        args.replacement,
        recursive=args.recursive
    )

    print(f"Renamed {len(renamed)} files:")
    for path in renamed:
        print(f"  {path}")

    return 0


def main():
    """Main CLI entry point."""
    parser = setup_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    command_handlers = {
        'organize': handle_organize,
        'search': handle_search,
        'duplicates': handle_duplicates,
        'cleanup': handle_cleanup,
        'rename': handle_rename
    }

    try:
        handler = command_handlers.get(args.command)
        if handler:
            return handler(args)
        else:
            print(f"Error: Unknown command '{args.command}'", file=sys.stderr)
            return 1
            
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
