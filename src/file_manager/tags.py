"""
Tagging system for file management.
Uses SQLite to store tags associated with files.
"""

import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

class TagManager:
    """Manages file tags using a local SQLite database."""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            self.db_path = Path.home() / ".tfm" / "tags.db"
        else:
            self.db_path = db_path

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize the database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")

        # Tags table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        """)

        # Files table
        # We store normalized absolute paths
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT UNIQUE NOT NULL
            )
        """)

        # Join table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS file_tags (
                file_id INTEGER,
                tag_id INTEGER,
                PRIMARY KEY (file_id, tag_id),
                FOREIGN KEY (file_id) REFERENCES files (id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE
            )
        """)

        conn.commit()
        conn.close()

    def add_tag(self, file_path: Path, tag: str) -> bool:
        """Add a tag to a file."""
        abs_path = str(file_path.resolve())
        tag = tag.lower().strip()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # ensure file exists in DB
            cursor.execute("INSERT OR IGNORE INTO files (path) VALUES (?)", (abs_path,))
            file_id_row = cursor.execute("SELECT id FROM files WHERE path = ?", (abs_path,)).fetchone()
            file_id = file_id_row[0]

            # ensure tag exists in DB
            cursor.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag,))
            tag_id_row = cursor.execute("SELECT id FROM tags WHERE name = ?", (tag,)).fetchone()
            tag_id = tag_id_row[0]

            # link them
            cursor.execute("INSERT OR IGNORE INTO file_tags (file_id, tag_id) VALUES (?, ?)", (file_id, tag_id))
            conn.commit()
            return True
        except Exception as e:
            logging.error(f"Failed to add tag: {e}")
            return False
        finally:
            conn.close()

    def remove_tag(self, file_path: Path, tag: str) -> bool:
        """Remove a tag from a file."""
        abs_path = str(file_path.resolve())
        tag = tag.lower().strip()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                DELETE FROM file_tags
                WHERE file_id = (SELECT id FROM files WHERE path = ?)
                AND tag_id = (SELECT id FROM tags WHERE name = ?)
            """, (abs_path, tag))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Failed to remove tag: {e}")
            return False
        finally:
            conn.close()

    def get_tags_for_file(self, file_path: Path) -> List[str]:
        """Get all tags for a file."""
        abs_path = str(file_path.resolve())

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT t.name FROM tags t
                JOIN file_tags ft ON t.id = ft.tag_id
                JOIN files f ON f.id = ft.file_id
                WHERE f.path = ?
            """, (abs_path,))
            return [row[0] for row in cursor.fetchall()]
        except Exception:
            return []
        finally:
            conn.close()

    def get_files_by_tag(self, tag: str) -> List[Path]:
        """Get all files with a specific tag."""
        tag = tag.lower().strip()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT f.path FROM files f
                JOIN file_tags ft ON f.id = ft.file_id
                JOIN tags t ON t.id = ft.tag_id
                WHERE t.name = ?
            """, (tag,))
            return [Path(row[0]) for row in cursor.fetchall()]
        except Exception:
            return []
        finally:
            conn.close()

    def list_all_tags(self) -> List[str]:
        """List all unique tags."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT name FROM tags ORDER BY name")
            return [row[0] for row in cursor.fetchall()]
        except Exception:
            return []
        finally:
            conn.close()

    def suggest_tags(self, file_path: Path) -> List[str]:
        """Suggest tags based on filename, extension, or context (simple rule-based for now)."""
        suggestions = []
        name = file_path.name.lower()
        ext = file_path.suffix.lower()

        # Extension based
        if ext in ['.jpg', '.png', '.gif']:
            suggestions.append('image')
        elif ext in ['.pdf', '.doc', '.docx']:
            suggestions.append('document')
        elif ext in ['.py', '.js', '.c']:
            suggestions.append('code')

        # Keyword based
        if 'work' in name:
            suggestions.append('work')
        if 'personal' in name:
            suggestions.append('personal')
        if 'invoice' in name:
            suggestions.append('finance')

        return suggestions
