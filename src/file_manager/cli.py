#!/usr/bin/env python3
"""
Command-line interface for automation features.
This provides batch operations without the TUI.
"""

import argparse
import sys
import json
from pathlib import Path

try:
    from .automation import FileOrganizer
    from .search import FileSearcher
    from .tags import TagManager
    from .scheduler import TaskScheduler
except ImportError:
    # Support running directly
    from automation import FileOrganizer
    from search import FileSearcher
    from tags import TagManager
    from scheduler import TaskScheduler


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

  # Manage tags
  tfm-auto tags --list
  tfm-auto tags --search work
  tfm-auto tags --add path/to/file --tag work

  # Manage schedule
  tfm-auto schedule --add "Daily Cleanup" --cron "0 0 * * *" --target ~/Downloads --type cleanup --params '{"days": 30}'
  tfm-auto schedule --list
  tfm-auto schedule --run-now
  tfm-auto schedule --daemon
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
    search_parser.add_argument('--tag', help='Search by tag')
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
    
    # Tags command
    tags_parser = subparsers.add_parser('tags', help='Manage file tags')
    tags_parser.add_argument('--list', action='store_true', help='List all tags')
    tags_parser.add_argument('--search', help='Search files by tag')
    tags_parser.add_argument('--export', action='store_true', help='Export all tags and files')
    tags_parser.add_argument('--add', help='Add a tag to a file (requires --tag)')
    tags_parser.add_argument('--remove', help='Remove a tag from a file (requires --tag)')
    tags_parser.add_argument('--tag', help='Tag name to add/remove')

    # Schedule command
    sched_parser = subparsers.add_parser('schedule', help='Manage scheduled tasks')
    sched_parser.add_argument('--add', help='Task name')
    sched_parser.add_argument('--cron', help='Cron expression')
    sched_parser.add_argument('--target', help='Target directory')
    sched_parser.add_argument('--type', help='Task type (cleanup, organize_by_type, organize_by_date, find_duplicates)')
    sched_parser.add_argument('--params', help='JSON string of parameters')
    sched_parser.add_argument('--list', action='store_true', help='List all scheduled tasks')
    sched_parser.add_argument('--remove', help='Remove task by name')
    sched_parser.add_argument('--run-now', action='store_true', help='Run pending tasks immediately')
    sched_parser.add_argument('--daemon', action='store_true', help='Run scheduler as a daemon')

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

    if args.tag:
        results = searcher.search_by_tag(args.tag)
        print(f"Found {len(results)} files tagged with '{args.tag}':")
        for path in results:
            print(f"  {path}")
        return 0

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
        print("Error: Specify --name, --content, or --tag")
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

def handle_tags(args):
    """Handle the tags command."""
    tm = TagManager()

    if args.list:
        tags = tm.list_all_tags()
        print("Available Tags:")
        for tag in tags:
            print(f"  {tag}")

    elif args.search:
        files = tm.get_files_by_tag(args.search)
        print(f"Files tagged '{args.search}':")
        for path in files:
            print(f"  {path}")

    elif args.export:
        tags = tm.list_all_tags()
        export_data = {}
        for tag in tags:
            files = [str(p) for p in tm.get_files_by_tag(tag)]
            export_data[tag] = files
        print(json.dumps(export_data, indent=2))

    elif args.add:
        if not args.tag:
            print("Error: --tag is required with --add")
            return 1
        path = Path(args.add)
        if not path.exists():
            print(f"Error: File not found: {path}")
            return 1
        if tm.add_tag(path, args.tag):
            print(f"Added tag '{args.tag}' to {path}")
        else:
            print(f"Failed to add tag.")

    elif args.remove:
        if not args.tag:
            print("Error: --tag is required with --remove")
            return 1
        path = Path(args.remove)
        if tm.remove_tag(path, args.tag):
            print(f"Removed tag '{args.tag}' from {path}")
        else:
            print(f"Failed to remove tag (or tag/file not found).")

    else:
        print("Error: Specify an action (--list, --search, --export, --add, --remove)")
        return 1

    return 0

def handle_schedule(args):
    """Handle the schedule command."""
    scheduler = TaskScheduler()

    if args.add:
        if not args.cron or not args.target or not args.type:
            print("Error: --cron, --target, and --type are required with --add")
            return 1

        params = {}
        if args.params:
            try:
                params = json.loads(args.params)
            except json.JSONDecodeError:
                print("Error: Invalid JSON for --params")
                return 1

        if scheduler.add_task(args.add, args.cron, args.target, args.type, params):
            print(f"Task '{args.add}' added.")
        else:
            print(f"Failed to add task.")

    elif args.remove:
        if scheduler.remove_task(args.remove):
            print(f"Task '{args.remove}' removed.")
        else:
            print(f"Failed to remove task (or not found).")

    elif args.list:
        tasks = scheduler.list_tasks()
        print("Scheduled Tasks:")
        for task in tasks:
            print(f"  {task['name']}: {task['cron']} ({task['task_type']}) - Last run: {task.get('last_run', 'Never')}")

    elif args.run_now:
        print("Running pending tasks...")
        scheduler.run_pending_tasks()
        print("Done.")

    elif args.daemon:
        scheduler.run_daemon()

    else:
        print("Error: Specify an action (--add, --remove, --list, --run-now, --daemon)")
        return 1

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
        'rename': handle_rename,
        'tags': handle_tags,
        'schedule': handle_schedule
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
