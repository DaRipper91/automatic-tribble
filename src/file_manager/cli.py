#!/usr/bin/env python3
"""
Command-line interface for automation features.
"""

import asyncio
import argparse
import sys
import json
import os
import subprocess
from pathlib import Path
from typing import Optional

# Import rich for progress bars
try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
    from rich.table import Table
except ImportError:
    print("Error: 'rich' library is required. Please install it.", file=sys.stderr)
    sys.exit(1)

from .automation import FileOrganizer, ConflictResolutionStrategy
from .search import FileSearcher
from .file_operations import FileOperations
from .config import ConfigManager

console = Console()

def setup_parser():
    """Set up the argument parser."""
    parser = argparse.ArgumentParser(
        description="File Manager - Automation CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--undo', action='store_true', help='Undo last operation')
    parser.add_argument('--redo', action='store_true', help='Redo last operation')
    parser.add_argument('--json', action='store_true', help='Output in JSON format')

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Organize command
    organize = subparsers.add_parser('organize', help='Organize files')
    organize.add_argument('--source', required=True, help='Source directory')
    organize.add_argument('--target', required=True, help='Target directory')
    organize.add_argument('--by-type', action='store_true', help='Organize by file type')
    organize.add_argument('--by-date', action='store_true', help='Organize by date')
    organize.add_argument('--move', action='store_true', help='Move files instead of copy')
    
    # Search command
    search = subparsers.add_parser('search', help='Search for files')
    search.add_argument('--dir', required=True, help='Directory to search')
    search.add_argument('--name', help='File name pattern')
    search.add_argument('--content', help='Search file contents')
    search.add_argument('--case-sensitive', action='store_true', help='Case sensitive search')
    
    # Duplicates command
    dup = subparsers.add_parser('duplicates', help='Find duplicate files')
    dup.add_argument('--dir', required=True, help='Directory to search')
    dup.add_argument('--recursive', action='store_true', default=True, help='Search recursively')
    dup.add_argument('--resolve', choices=['newest', 'oldest', 'interactive'], help='Resolve duplicates strategy')
    
    # Cleanup command
    cleanup = subparsers.add_parser('cleanup', help='Clean up old files')
    cleanup.add_argument('--dir', required=True, help='Directory to clean')
    cleanup.add_argument('--days', type=int, required=True, help='Delete files older than N days')
    cleanup.add_argument('--dry-run', action='store_true', help='Show what would be deleted without deleting')
    cleanup.add_argument('--recursive', action='store_true', help='Search recursively')
    
    # Rename command
    rename = subparsers.add_parser('rename', help='Batch rename files')
    rename.add_argument('--dir', required=True, help='Directory containing files')
    rename.add_argument('--pattern', required=True, help='Text pattern to match')
    rename.add_argument('--replacement', required=True, help='Replacement text')
    rename.add_argument('--recursive', action='store_true', help='Process subdirectories')

    # Config command
    config = subparsers.add_parser('config', help='Manage configuration')
    config.add_argument('--edit', action='store_true', help='Edit configuration file')

    # Tag command
    tag_parser = subparsers.add_parser('tags', help='Manage file tags')
    tag_parser.add_argument('--list', action='store_true', help='List all tags')
    tag_parser.add_argument('--search', help='Search for files with tag')
    tag_parser.add_argument('--add', nargs=2, metavar=('FILE', 'TAG'), help='Add tag to file')
    tag_parser.add_argument('--remove', nargs=2, metavar=('FILE', 'TAG'), help='Remove tag from file')
    tag_parser.add_argument('--get', metavar='FILE', help='Get tags for file')
    tag_parser.add_argument('--export', action='store_true', help='Export tags (not implemented)')

    # Schedule command
    schedule_parser = subparsers.add_parser('schedule', help='Manage scheduled tasks')
    schedule_parser.add_argument('--add', help='Task name')
    schedule_parser.add_argument('--cron', help='Cron expression')
    schedule_parser.add_argument('--type', choices=['organize_by_type', 'organize_by_date', 'cleanup'], help='Task type')
    schedule_parser.add_argument('--source', help='Source directory')
    schedule_parser.add_argument('--target', help='Target directory (for organize)')
    schedule_parser.add_argument('--days', type=int, help='Days (for cleanup)')
    schedule_parser.add_argument('--list', action='store_true', help='List tasks')
    schedule_parser.add_argument('--remove', help='Remove task by name')
    schedule_parser.add_argument('--run-now', action='store_true', help='Run due tasks immediately')
    schedule_parser.add_argument('--daemon', action='store_true', help='Run scheduler as daemon')
    
    return parser

async def monitor_progress(queue: asyncio.Queue, task_description: str, total: Optional[int] = None):
    """Monitor progress queue and update rich progress bar."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeRemainingColumn(),
        console=console
    ) as progress:
        task_id = progress.add_task(task_description, total=total)

        while True:
            item = await queue.get()
            if item is None:
                break

            progress.console.print(f"Processed: {item}")
            progress.advance(task_id)

async def handle_organize(args):
    organizer = FileOrganizer()
    source = Path(args.source)
    target = Path(args.target)

    if not source.exists():
        if args.json:
             print(json.dumps({"error": f"Source directory does not exist: {source}"}))
        else:
             console.print(f"[bold red]Error:[/bold red] Source directory does not exist: {source}")
        return 1

    progress_queue = asyncio.Queue() if not args.json else None

    task = None
    if args.by_type:
        task = asyncio.create_task(organizer.organize_by_type(source, target, move=args.move, progress_queue=progress_queue))
    elif args.by_date:
        task = asyncio.create_task(organizer.organize_by_date(source, target, move=args.move, progress_queue=progress_queue))
    else:
        if args.json:
            print(json.dumps({"error": "Specify --by-type or --by-date"}))
        else:
            console.print("[bold red]Error:[/bold red] Specify either --by-type or --by-date")
        return 1

    if progress_queue:
        monitor_task = asyncio.create_task(monitor_progress(progress_queue, "Organizing files..."))
        result = await task
        await progress_queue.put(None)
        await monitor_task
    else:
        result = await task

    # Summary
    if args.json:
        # result is Dict[str, List[Path]]
        # Convert Path to str
        json_result = {k: [str(p) for p in v] for k, v in result.items()}
        print(json.dumps(json_result, indent=2))
    else:
        table = Table(title="Organization Summary")
        table.add_column("Category", style="cyan")
        table.add_column("Count", style="green")

        for category, files in result.items():
            table.add_row(category, str(len(files)))

        console.print(table)

    return 0

async def handle_search(args):
    searcher = FileSearcher()
    directory = Path(args.dir)

    if not directory.exists():
        if args.json:
             print(json.dumps({"error": f"Directory does not exist: {directory}"}))
        else:
             console.print(f"[bold red]Error:[/bold red] Directory does not exist: {directory}")
        return 1

    results = []
    if args.name:
        results = searcher.search_by_name(directory, args.name, case_sensitive=args.case_sensitive)
    elif args.content:
        results = searcher.search_by_content(directory, args.content, case_sensitive=args.case_sensitive)

    if args.json:
        print(json.dumps([str(p) for p in results], indent=2))
    else:
        console.print(f"Found {len(results)} files:")
        for path in results:
            console.print(f"  {path}")
    return 0

async def handle_duplicates(args):
    organizer = FileOrganizer()
    directory = Path(args.dir)

    progress_queue = asyncio.Queue() if not args.json else None

    duplicates = await organizer.find_duplicates(directory, recursive=args.recursive)

    if args.resolve:
        strategy = ConflictResolutionStrategy.INTERACTIVE
        if args.resolve == 'newest':
            strategy = ConflictResolutionStrategy.KEEP_NEWEST
        elif args.resolve == 'oldest':
            strategy = ConflictResolutionStrategy.KEEP_OLDEST

        if strategy == ConflictResolutionStrategy.INTERACTIVE:
             if args.json:
                 pass
             else:
                 console.print("Interactive mode not supported in CLI.")
        else:
             deleted = await organizer.resolve_duplicates(duplicates, strategy, progress_queue)
             if args.json:
                 print(json.dumps({"deleted": [str(p) for p in deleted]}, indent=2))
             else:
                 console.print(f"Resolved duplicates. Deleted {len(deleted)} files.")
             return 0

    if args.json:
        # Convert Path to str
        json_result = {k: [str(p) for p in v] for k, v in duplicates.items()}
        print(json.dumps(json_result, indent=2))
    else:
        if duplicates:
            console.print(f"Found {len(duplicates)} groups of duplicate files:")
            for hash_val, files in duplicates.items():
                console.print(f"\n  Duplicate group ({len(files)} files):", style="bold yellow")
                for path in files:
                    console.print(f"    {path}")
        else:
            console.print("No duplicates found.")
    return 0

async def handle_cleanup(args):
    organizer = FileOrganizer()
    directory = Path(args.dir)

    progress_queue = asyncio.Queue() if not args.json else None

    # Start task
    task = asyncio.create_task(organizer.cleanup_old_files(
        directory, args.days, args.recursive, args.dry_run, progress_queue
    ))

    if progress_queue:
        monitor_task = asyncio.create_task(monitor_progress(progress_queue, "Cleaning up files..."))
        old_files = await task
        await progress_queue.put(None)
        await monitor_task
    else:
        old_files = await task

    if args.json:
        print(json.dumps([str(p) for p in old_files], indent=2))
    else:
        action = "Would delete" if args.dry_run else "Deleted"
        console.print(f"{action} {len(old_files)} files:")
        for path in old_files:
            console.print(f"  {path}")
    return 0

async def handle_rename(args):
    organizer = FileOrganizer()
    directory = Path(args.dir)

    progress_queue = asyncio.Queue() if not args.json else None

    task = asyncio.create_task(organizer.batch_rename(
        directory, args.pattern, args.replacement, args.recursive, progress_queue
    ))

    if progress_queue:
        monitor_task = asyncio.create_task(monitor_progress(progress_queue, "Renaming files..."))
        renamed = await task
        await progress_queue.put(None)
        await monitor_task
    else:
        renamed = await task

    if args.json:
        print(json.dumps([str(p) for p in renamed], indent=2))
    else:
        console.print(f"Renamed {len(renamed)} files:")
        for path in renamed:
            console.print(f"  {path}")
    return 0

async def handle_undo(args):
    file_ops = FileOperations()
    result = await file_ops.undo_last()
    if args.json:
        print(json.dumps({"result": result}))
    else:
        console.print(f"[bold]Undo Result:[/bold] {result}")

async def handle_redo(args):
    file_ops = FileOperations()
    result = await file_ops.redo_last()
    if args.json:
        print(json.dumps({"result": result}))
    else:
        console.print(f"[bold]Redo Result:[/bold] {result}")

async def handle_config(args):
    config_manager = ConfigManager()
    config_path = config_manager.get_config_path()

    if args.edit:
        editor = os.environ.get('EDITOR', 'nano')
        subprocess.call([editor, str(config_path)])
    else:
        console.print(f"Configuration file: {config_path}")
        categories = config_manager.load_categories()
        console.print(categories)

async def handle_tags(args):
    from .tags import TagManager
    manager = TagManager()

    if args.list:
        tags = manager.list_all_tags()
        if args.json:
            print(json.dumps(tags))
        else:
            console.print("Available Tags:")
            for t in tags:
                console.print(f"  {t}")

    elif args.search:
        files = manager.search_by_tag(args.search)
        if args.json:
            print(json.dumps([str(p) for p in files]))
        else:
            console.print(f"Files tagged with '{args.search}':")
            for p in files:
                console.print(f"  {p}")

    elif args.add:
        file_path = Path(args.add[0])
        tag = args.add[1]
        success = manager.add_tag(file_path, tag)
        if args.json:
            print(json.dumps({"success": success}))
        else:
            if success:
                console.print(f"Added tag '{tag}' to {file_path}")
            else:
                console.print(f"[red]Failed to add tag to {file_path}[/]")

    elif args.remove:
        file_path = Path(args.remove[0])
        tag = args.remove[1]
        success = manager.remove_tag(file_path, tag)
        if args.json:
            print(json.dumps({"success": success}))
        else:
            if success:
                console.print(f"Removed tag '{tag}' from {file_path}")
            else:
                console.print(f"[red]Failed to remove tag from {file_path}[/]")

    elif args.get:
        file_path = Path(args.get)
        tags = manager.get_tags(file_path)
        if args.json:
            print(json.dumps(tags))
        else:
            console.print(f"Tags for {file_path}:")
            for t in tags:
                console.print(f"  {t}")

    else:
        pass

    return 0

async def handle_schedule(args):
    from .scheduler import TaskScheduler
    scheduler = TaskScheduler()

    if args.daemon:
        await scheduler.run_daemon()
        return 0

    if args.add:
        if not args.cron or not args.type:
            console.print("[red]--cron and --type are required for adding a task.[/]")
            return 1

        params = {}
        if args.type.startswith("organize"):
            if not args.source or not args.target:
                console.print("[red]--source and --target are required for organize tasks.[/]")
                return 1
            params = {"source": args.source, "target": args.target}
        elif args.type == "cleanup":
             if not args.source or not args.days:
                console.print("[red]--source (as --dir) and --days are required for cleanup tasks.[/]")
                return 1
             params = {"dir": args.source, "days": args.days, "recursive": True}

        success = scheduler.add_task(args.add, args.cron, args.type, params)
        if success:
            console.print(f"Task '{args.add}' scheduled.")
        else:
             console.print(f"[red]Failed to schedule task '{args.add}'. Check name or cron expression.[/]")

    elif args.remove:
        success = scheduler.remove_task(args.remove)
        if success:
            console.print(f"Task '{args.remove}' removed.")
        else:
             console.print(f"[red]Task '{args.remove}' not found.[/]")

    elif args.list:
        tasks = scheduler.list_tasks()
        if args.json:
            print(json.dumps(tasks, indent=2))
        else:
            table = Table(title="Scheduled Tasks")
            table.add_column("Name")
            table.add_column("Cron")
            table.add_column("Type")
            table.add_column("Last Run")
            for t in tasks:
                table.add_row(t["name"], t["cron"], t["type"], str(t.get("last_run", "Never")))
            console.print(table)

    elif args.run_now:
        await scheduler.run_due_tasks()
        console.print("Checked and executed due tasks.")

    else:
        # Check if run as daemon via direct invocation, or just show help
        pass

    return 0

async def main_async():
    parser = setup_parser()
    args = parser.parse_args()
    
    if args.undo:
        await handle_undo(args)
        return 0
    if args.redo:
        await handle_redo(args)
        return 0

    if not args.command:
        parser.print_help()
        return 1
    
    command_handlers = {
        'organize': handle_organize,
        'search': handle_search,
        'duplicates': handle_duplicates,
        'cleanup': handle_cleanup,
        'rename': handle_rename,
        'config': handle_config,
        'tags': handle_tags,
        'schedule': handle_schedule
    }

    handler = command_handlers.get(args.command)
    if handler:
        try:
            return await handler(args)
        except Exception as e:
            if args.json:
                 print(json.dumps({"error": str(e)}))
            else:
                 console.print(f"[bold red]Error:[/bold red] {str(e)}")
            return 1
    else:
        return 1

def main():
    try:
        sys.exit(asyncio.run(main_async()))
    except KeyboardInterrupt:
        sys.exit(1)

if __name__ == '__main__':
    main()
