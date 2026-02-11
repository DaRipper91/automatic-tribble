#!/usr/bin/env python3
"""
Example script demonstrating the automation features.
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from file_manager.automation import FileOrganizer
from file_manager.search import FileSearcher
from file_manager.file_operations import FileOperations


def demo_search():
    """Demonstrate search functionality."""
    print("=" * 60)
    print("DEMO: File Search")
    print("=" * 60)
    
    searcher = FileSearcher()
    
    # Search by name
    print("\n1. Searching for Python files in current directory...")
    results = searcher.search_by_name(Path.cwd(), "*.py", recursive=False)
    print(f"   Found {len(results)} Python files")
    
    # Search by size
    print("\n2. Searching for files larger than 1KB...")
    results = searcher.search_by_size(Path.cwd(), min_size=1024, recursive=False)
    print(f"   Found {len(results)} files")


def demo_organization():
    """Demonstrate file organization."""
    print("\n" + "=" * 60)
    print("DEMO: File Organization")
    print("=" * 60)
    
    organizer = FileOrganizer()
    
    # Show file categories
    print("\n1. Available file categories:")
    for category, extensions in organizer.FILE_CATEGORIES.items():
        print(f"   {category}: {', '.join(extensions[:5])}...")
    
    print("\n2. File organization can:")
    print("   - Organize by type (images, videos, documents, etc.)")
    print("   - Organize by date (year/month folders)")
    print("   - Find and remove duplicates")
    print("   - Batch rename files")
    print("   - Clean up old files")


def demo_file_operations():
    """Demonstrate file operations."""
    print("\n" + "=" * 60)
    print("DEMO: File Operations")
    print("=" * 60)
    
    file_ops = FileOperations()
    
    print("\n1. Available operations:")
    print("   - Copy files and directories")
    print("   - Move files and directories")
    print("   - Delete files and directories")
    print("   - Create new directories")
    print("   - Rename files and directories")
    print("   - Get file/directory sizes")
    
    # Demo size formatting
    print("\n2. Size formatting examples:")
    sizes = [512, 1024, 1024*1024, 1024*1024*1024]
    for size in sizes:
        formatted = file_ops.format_size(size)
        print(f"   {size} bytes = {formatted}")


def main():
    """Run all demos."""
    print("\n" + "╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "File Manager - Feature Demo" + " " * 15 + "║")
    print("╚" + "=" * 58 + "╝")
    
    demo_search()
    demo_organization()
    demo_file_operations()
    
    print("\n" + "=" * 60)
    print("To use the TUI, run: python run.py")
    print("To use automation CLI, run: python src/file_manager/cli.py --help")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
