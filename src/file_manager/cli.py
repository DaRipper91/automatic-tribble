#!/usr/bin/env python3
"""
Command-line interface for automation features.
"""

import asyncio
import argparse
import sys
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List

# Import rich for progress bars
try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
    from rich.table import Table
    from rich.prompt import Prompt
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

            # If item is a string, it's a status update, otherwise it's a Path
            msg = str(item)
            # Truncate if too long
            if len(msg) > 80:
                msg = "..." + msg[-77:]

            progress.console.print(f"Processed: {msg}")
            progress.advance(task_id)

def handle_interactive_resolution(files: List[Path]) -> List[Path]:
    """Callback for interactive duplicate resolution."""
    console.print("\nDuplicate Group found:", style="bold yellow")
    for i, file in enumerate(files):
        try:
            size_str = FileOperations.format_size(file.stat().st_size)
            mtime_str = datetime.fromtimestamp(file.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            console.print(f"  {i+1}. {file} (Size: {size_str}, Modified: {mtime_str})")
        except OSError:
             console.print(f"  {i+1}. {file} (Error reading file)")

    choices = [str(i+1) for i in range(len(files))] + ["s"]

    while True:
        selection = Prompt.ask("Select file to [bold green]KEEP[/bold green] (enter number), or [bold red]s[/bold red]kip", choices=choices, default="s")
        if selection.lower() == 's':
            return [] # Keep all (delete none)

        try:
            idx = int(selection) - 1
            if 0 <= idx < len(files):
                # Return all files EXCEPT the selected one (files to delete)
                return [f for i, f in enumerate(files) if i != idx]
        except ValueError:
            pass
    return []

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

    # Search phase
    task = asyncio.create_task(organizer.find_duplicates(directory, recursive=args.recursive, progress_queue=progress_queue))

    if progress_queue:
        monitor_task = asyncio.create_task(monitor_progress(progress_queue, "Scanning for duplicates..."))
        duplicates = await task
        await progress_queue.put(None)
        await monitor_task
    else:
        duplicates = await task

    if args.resolve:
        strategy = ConflictResolutionStrategy.INTERACTIVE
        if args.resolve == 'newest':
            strategy = ConflictResolutionStrategy.KEEP_NEWEST
        elif args.resolve == 'oldest':
            strategy = ConflictResolutionStrategy.KEEP_OLDEST
        # Note: interactive is default if resolve is set but not newest/oldest?
        # Actually argparse choices handles validation, so here we assume it maps correctly.
        # But wait, choices in setup_parser only listed newest, oldest, interactive.
        elif args.resolve == 'interactive':
            strategy = ConflictResolutionStrategy.INTERACTIVE

        interactive_cb = None
        if strategy == ConflictResolutionStrategy.INTERACTIVE:
             if args.json:
                 print(json.dumps({"error": "Interactive mode not supported with --json"}))
                 return 1
             else:
                 interactive_cb = handle_interactive_resolution

        # Resolution phase
        progress_queue = asyncio.Queue() if not args.json else None

        resolve_task = asyncio.create_task(organizer.resolve_duplicates(
            duplicates, strategy, progress_queue, interactive_callback=interactive_cb
        ))

        if progress_queue:
             monitor_task = asyncio.create_task(monitor_progress(progress_queue, "Resolving duplicates..."))
             deleted = await resolve_task
             await progress_queue.put(None)
             await monitor_task
        else:
             deleted = await resolve_task

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
        try:
            process = await asyncio.create_subprocess_exec(editor, str(config_path))
            await process.wait()
        except FileNotFoundError:
             console.print(f"[bold red]Error:[/bold red] Editor '{editor}' not found.")
    else:
        console.print(f"Configuration file: {config_path}")
        categories = config_manager.load_categories()
        console.print(categories)

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
        'config': handle_config
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
