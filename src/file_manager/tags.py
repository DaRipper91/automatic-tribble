"""
Tagging system for File Manager.
"""

import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class TagManager:
    """Manages file tags using a SQLite database."""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            # Default to ~/.tfm/tags.db
            home = Path.home()
            tfm_dir = home / ".tfm"
            tfm_dir.mkdir(exist_ok=True)
            self.db_path = tfm_dir / "tags.db"
        else:
            self.db_path = db_path

        self._init_db()

    def _init_db(self):
        """Initialize the database schema."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tags (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        file_path TEXT NOT NULL,
                        tag TEXT NOT NULL,
                        UNIQUE(file_path, tag)
                    )
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_tag ON tags (tag)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_file_path ON tags (file_path)")
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Failed to initialize tags database: {e}")

    def add_tag(self, file_path: Path, tag: str) -> bool:
        """Add a tag to a file."""
        path_str = str(file_path.resolve())
        tag = tag.strip()
        if not tag:
            return False

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR IGNORE INTO tags (file_path, tag) VALUES (?, ?)",
                    (path_str, tag)
                )
                conn.commit()
                return True
        except sqlite3.Error as e:
            logger.error(f"Failed to add tag: {e}")
            return False

    def remove_tag(self, file_path: Path, tag: str) -> bool:
        """Remove a tag from a file."""
        path_str = str(file_path.resolve())
        tag = tag.strip()

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM tags WHERE file_path = ? AND tag = ?",
                    (path_str, tag)
                )
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Failed to remove tag: {e}")
            return False

    def get_tags_for_file(self, file_path: Path) -> List[str]:
        """Get all tags for a file."""
        path_str = str(file_path.resolve())

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT tag FROM tags WHERE file_path = ?",
                    (path_str,)
                )
                return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Failed to get tags for file: {e}")
            return []

    def get_files_by_tag(self, tag: str) -> List[Path]:
        """Get all files with a specific tag."""
        tag = tag.strip()

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT file_path FROM tags WHERE tag = ?",
                    (tag,)
                )
                paths = []
                for row in cursor.fetchall():
                    p = Path(row[0])
                    # Optional: Check if file exists? Maybe not, keep broken links until cleanup
                    paths.append(p)
                return paths
        except sqlite3.Error as e:
            logger.error(f"Failed to get files by tag: {e}")
            return []

    def list_all_tags(self) -> List[Tuple[str, int]]:
        """List all tags and their usage count."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT tag, COUNT(*) FROM tags GROUP BY tag ORDER BY COUNT(*) DESC"
                )
                return cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Failed to list tags: {e}")
            return []

    def cleanup_missing_files(self) -> int:
        """Remove entries for files that no longer exist."""
        removed_count = 0
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT file_path FROM tags")
                files = cursor.fetchall()

                for (path_str,) in files:
                    if not Path(path_str).exists():
                        cursor.execute("DELETE FROM tags WHERE file_path = ?", (path_str,))
                        removed_count += cursor.rowcount

                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Failed to cleanup tags: {e}")

        return removed_count

    def get_all_tags_export(self) -> Dict[str, List[str]]:
        """Export all tags as a dictionary {file_path: [tags]}."""
        export_data = {}
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT file_path, tag FROM tags ORDER BY file_path")
                for path_str, tag in cursor.fetchall():
                    if path_str not in export_data:
                        export_data[path_str] = []
                    export_data[path_str].append(tag)
        except sqlite3.Error as e:
            logger.error(f"Failed to export tags: {e}")
        return export_data
