"""
File Tagging System backed by SQLite.
"""

import sqlite3
import asyncio
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from .logger import get_logger

logger = get_logger("tags")

class TagManager:
    """Manages file tags using a local SQLite database."""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            db_path = Path.home() / ".tfm" / "tags.db"
        self.db_path = db_path
        self._ensure_db()

    def _ensure_db(self) -> None:
        """Ensure database and tables exist."""
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS files (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        path TEXT UNIQUE NOT NULL,
                        mtime REAL
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS tags (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE NOT NULL
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS file_tags (
                        file_id INTEGER,
                        tag_id INTEGER,
                        PRIMARY KEY (file_id, tag_id),
                        FOREIGN KEY(file_id) REFERENCES files(id) ON DELETE CASCADE,
                        FOREIGN KEY(tag_id) REFERENCES tags(id) ON DELETE CASCADE
                    )
                """)
        except sqlite3.Error as e:
            logger.error(f"Database init error: {e}")

    def add_tag(self, file_path: Path, tag: str) -> bool:
        """Add a tag to a file."""
        file_path = file_path.resolve()
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Ensure file exists in DB
                try:
                    mtime = file_path.stat().st_mtime
                except OSError:
                    mtime = 0.0

                conn.execute(
                    "INSERT OR IGNORE INTO files (path, mtime) VALUES (?, ?)",
                    (str(file_path), mtime)
                )
                file_id = conn.execute("SELECT id FROM files WHERE path = ?", (str(file_path),)).fetchone()[0]

                # Ensure tag exists
                conn.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag,))
                tag_id = conn.execute("SELECT id FROM tags WHERE name = ?", (tag,)).fetchone()[0]

                # Link
                conn.execute("INSERT OR IGNORE INTO file_tags (file_id, tag_id) VALUES (?, ?)", (file_id, tag_id))
                return True
        except (sqlite3.Error, OSError) as e:
            logger.error(f"Error adding tag: {e}")
            return False

    def remove_tag(self, file_path: Path, tag: str) -> bool:
        """Remove a tag from a file."""
        file_path = file_path.resolve()
        try:
            with sqlite3.connect(self.db_path) as conn:
                file_row = conn.execute("SELECT id FROM files WHERE path = ?", (str(file_path),)).fetchone()
                if not file_row:
                    return False
                file_id = file_row[0]

                tag_row = conn.execute("SELECT id FROM tags WHERE name = ?", (tag,)).fetchone()
                if not tag_row:
                    return False
                tag_id = tag_row[0]

                conn.execute("DELETE FROM file_tags WHERE file_id = ? AND tag_id = ?", (file_id, tag_id))
                return True
        except sqlite3.Error as e:
            logger.error(f"Error removing tag: {e}")
            return False

    def get_tags(self, file_path: Path) -> List[str]:
        """Get all tags for a file."""
        file_path = file_path.resolve()
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT t.name FROM tags t
                    JOIN file_tags ft ON t.id = ft.tag_id
                    JOIN files f ON f.id = ft.file_id
                    WHERE f.path = ?
                """, (str(file_path),))
                return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error getting tags: {e}")
            return []

    def search_by_tag(self, tag: str) -> List[Path]:
        """Find all files with a specific tag."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT f.path FROM files f
                    JOIN file_tags ft ON f.id = ft.file_id
                    JOIN tags t ON t.id = ft.tag_id
                    WHERE t.name = ?
                """, (tag,))

                paths = []
                for row in cursor.fetchall():
                    p = Path(row[0])
                    if p.exists():
                        paths.append(p)
                return paths
        except sqlite3.Error as e:
            logger.error(f"Error searching by tag: {e}")
            return []

    def list_all_tags(self) -> List[str]:
        """List all defined tags."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT name FROM tags ORDER BY name")
                return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error listing tags: {e}")
            return []

    async def auto_tag(self, file_path: Path, ai_client) -> List[str]:
        """Automatically suggest and apply tags using AI."""
        # This requires the AI client to be passed in, or we assume it's available.
        # Ideally, this method just calls the AI client.
        tags = ai_client.suggest_tags(file_path)
        for tag in tags:
            self.add_tag(file_path, tag)
        return tags
