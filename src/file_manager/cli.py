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
from datetime import datetime
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
from .tags import TagManager
from .scheduler import TaskScheduler

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

    # Tags command
    tags = subparsers.add_parser('tags', help='Manage file tags')
    tags.add_argument('--add', nargs=2, metavar=('FILE', 'TAG'), help='Add tag to file')
    tags.add_argument('--remove', nargs=2, metavar=('FILE', 'TAG'), help='Remove tag from file')
    tags.add_argument('--list', action='store_true', help='List all tags')
    tags.add_argument('--search', metavar='TAG', help='List files with tag')
    tags.add_argument('--cleanup', action='store_true', help='Clean up missing files')

    # Schedule command
    schedule = subparsers.add_parser('schedule', help='Manage scheduled tasks')
    schedule.add_argument('--list', action='store_true', help='List scheduled jobs')
    schedule.add_argument('--add', nargs=4, metavar=('NAME', 'CRON', 'TYPE', 'PARAMS_JSON'), help='Add new job')
    schedule.add_argument('--remove', metavar='NAME', help='Remove job')
    schedule.add_argument('--daemon', action='store_true', help='Run scheduler daemon')
    
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
    manager = TagManager()

    if args.add:
        path = Path(args.add[0])
        tag = args.add[1]
        if not path.exists():
            console.print(f"[red]File not found: {path}[/]")
            return 1
        if manager.add_tag(path, tag):
            console.print(f"[green]Added tag '{tag}' to {path}[/]")
        else:
            console.print(f"[red]Failed to add tag.[/]")

    elif args.remove:
        path = Path(args.remove[0])
        tag = args.remove[1]
        if manager.remove_tag(path, tag):
             console.print(f"[green]Removed tag '{tag}' from {path}[/]")
        else:
             console.print(f"[yellow]Tag not found.[/]")

    elif args.list:
        tags = manager.list_all_tags()
        table = Table(title="All Tags")
        table.add_column("Tag", style="cyan")
        table.add_column("Count", style="green")
        for t, c in tags:
            table.add_row(t, str(c))
        console.print(table)

    elif args.search:
        files = manager.get_files_by_tag(args.search)
        console.print(f"Files with tag '[cyan]{args.search}[/]':")
        for f in files:
            console.print(f"  {f}")

    elif args.cleanup:
        count = manager.cleanup_missing_files()
        console.print(f"Removed {count} missing files from database.")

    return 0

async def handle_schedule(args):
    scheduler = TaskScheduler()

    if args.daemon:
        await scheduler.run_daemon()
        return 0

    if args.list:
        jobs = scheduler.list_jobs()
        table = Table(title="Scheduled Jobs")
        table.add_column("Name", style="bold")
        table.add_column("Cron", style="yellow")
        table.add_column("Type", style="cyan")
        table.add_column("Last Run", style="dim")

        for job in jobs:
            last_run = "Never"
            if job["last_run"]:
                last_run = datetime.fromtimestamp(job["last_run"]).strftime("%Y-%m-%d %H:%M")
            table.add_row(job["name"], job["cron"], job["type"], last_run)
        console.print(table)

    elif args.add:
        name, cron, type_, params_str = args.add
        try:
            params = json.loads(params_str)
        except json.JSONDecodeError:
            console.print("[red]Invalid JSON parameters.[/]")
            return 1

        if scheduler.add_job(name, cron, type_, params):
            console.print(f"[green]Job '{name}' added.[/]")
        else:
             console.print("[red]Failed to add job (invalid cron or type).[/]")

    elif args.remove:
        if scheduler.remove_job(args.remove):
            console.print(f"[green]Job '{args.remove}' removed.[/]")
        else:
            console.print(f"[yellow]Job '{args.remove}' not found.[/]")

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
