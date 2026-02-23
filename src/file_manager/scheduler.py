"""
Scheduler for automated file management tasks.
"""

import json
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from croniter import croniter

from .automation import FileOrganizer

# Configure logging
logging.basicConfig(
    filename=str(Path.home() / ".tfm" / "scheduler.log"),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TaskScheduler:
    """Manages scheduled automation tasks."""

    def __init__(self, schedule_file: Optional[Path] = None):
        if schedule_file is None:
            self.schedule_file = Path.home() / ".tfm" / "schedule.json"
        else:
            self.schedule_file = schedule_file

        self.schedule_file.parent.mkdir(parents=True, exist_ok=True)
        self.organizer = FileOrganizer()

    def _load_tasks(self) -> List[Dict[str, Any]]:
        if not self.schedule_file.exists():
            return []
        try:
            with open(self.schedule_file, "r") as f:
                return json.load(f)
        except Exception:
            return []

    def _save_tasks(self, tasks: List[Dict[str, Any]]):
        try:
            with open(self.schedule_file, "w") as f:
                json.dump(tasks, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save tasks: {e}")

    def add_task(self, name: str, cron_expression: str, target_dir: str, task_type: str, params: Dict[str, Any] = None) -> bool:
        """Add a new scheduled task."""
        if not croniter.is_valid(cron_expression):
            logger.error(f"Invalid cron expression: {cron_expression}")
            return False

        tasks = self._load_tasks()

        # Check if name exists
        for task in tasks:
            if task["name"] == name:
                logger.error(f"Task with name '{name}' already exists.")
                return False

        new_task = {
            "name": name,
            "cron": cron_expression,
            "target_dir": target_dir,
            "task_type": task_type,
            "params": params or {},
            "last_run": None,
            "enabled": True
        }

        tasks.append(new_task)
        self._save_tasks(tasks)
        logger.info(f"Task '{name}' added.")
        return True

    def remove_task(self, name: str) -> bool:
        """Remove a task by name."""
        tasks = self._load_tasks()
        initial_count = len(tasks)
        tasks = [t for t in tasks if t["name"] != name]

        if len(tasks) < initial_count:
            self._save_tasks(tasks)
            logger.info(f"Task '{name}' removed.")
            return True
        return False

    def list_tasks(self) -> List[Dict[str, Any]]:
        """List all scheduled tasks."""
        return self._load_tasks()

    def run_pending_tasks(self):
        """Check and run all pending tasks."""
        tasks = self._load_tasks()
        modified = False

        for task in tasks:
            if not task.get("enabled", True):
                continue

            last_run = task.get("last_run")
            cron = task["cron"]
            now = datetime.now()

            # Determine if due
            if last_run is None:
                # First run: check if cron matches current time?
                # Or just run if it hasn't run yet?
                # Usually cron runs at the next scheduled time.
                # If last_run is None, we assume it's new.
                # Let's say we set last_run to now when added? No.
                # We check if current time matches cron schedule relative to some base?
                # croniter get_prev/get_next based on now.
                # If last_run is None, we set it to now and wait for next interval.
                # Or we can treat it as never run.

                # Standard cron daemon logic: check if time matches current minute.
                # croniter.match(cron, now)
                is_due = croniter.match(cron, now)
            else:
                last_run_dt = datetime.fromisoformat(last_run)
                # Check if next scheduled time after last_run is in the past (i.e. due)
                # But we might have missed it if daemon was off.
                # Simple logic: get next run time from last_run.
                # If next_run <= now, it is due.
                iter = croniter(cron, last_run_dt)
                next_run = iter.get_next(datetime)
                is_due = next_run <= now

            if is_due:
                logger.info(f"Running task: {task['name']}")
                success = self._execute_task(task)
                if success:
                    task["last_run"] = now.isoformat()
                    modified = True

        if modified:
            self._save_tasks(tasks)

    def _execute_task(self, task: Dict[str, Any]) -> bool:
        """Execute a single task."""
        try:
            task_type = task["task_type"]
            target_dir = Path(task["target_dir"])
            params = task.get("params", {})

            if not target_dir.exists():
                logger.error(f"Task '{task['name']}': Target directory {target_dir} does not exist.")
                return False

            if task_type == "organize_by_type":
                self.organizer.organize_by_type(target_dir, target_dir / "Organized", move=True)
            elif task_type == "organize_by_date":
                self.organizer.organize_by_date(target_dir, target_dir / "Organized_Date", move=True)
            elif task_type == "cleanup":
                days = params.get("days", 30)
                self.organizer.cleanup_old_files(target_dir, days, recursive=False)
            elif task_type == "find_duplicates":
                # Just log them?
                dups = self.organizer.find_duplicates(target_dir)
                logger.info(f"Task '{task['name']}': Found {len(dups)} duplicate groups.")
            else:
                logger.error(f"Unknown task type: {task_type}")
                return False

            logger.info(f"Task '{task['name']}' completed successfully.")
            return True

        except Exception as e:
            logger.error(f"Task '{task['name']}' failed: {e}")
            return False

    def run_daemon(self):
        """Run the scheduler as a daemon process."""
        print("Scheduler daemon started. Press Ctrl+C to stop.")
        logger.info("Scheduler daemon started.")
        try:
            while True:
                self.run_pending_tasks()
                # Sleep for 60 seconds
                time.sleep(60)
        except KeyboardInterrupt:
            print("Stopping scheduler...")
            logger.info("Scheduler daemon stopped.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="TFM Scheduler Daemon")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon")
    args = parser.parse_args()

    if args.daemon:
        scheduler = TaskScheduler()
        scheduler.run_daemon()
