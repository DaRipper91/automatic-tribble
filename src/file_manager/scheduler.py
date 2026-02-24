"""
Task Scheduler for File Manager.
"""

import asyncio
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from croniter import croniter

from .automation import FileOrganizer
from .logger import get_logger

logger = get_logger("scheduler")

class TaskScheduler:
    """Manages scheduled automation tasks."""

    def __init__(self, schedule_file: Optional[Path] = None):
        if schedule_file is None:
            schedule_file = Path.home() / ".tfm" / "schedule.json"
        self.schedule_file = schedule_file
        self.organizer = FileOrganizer()
        self.tasks: List[Dict[str, Any]] = self._load_schedule()

    def _load_schedule(self) -> List[Dict[str, Any]]:
        if not self.schedule_file.exists():
            return []
        try:
            with open(self.schedule_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading schedule: {e}")
            return []

    def _save_schedule(self) -> None:
        try:
            self.schedule_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.schedule_file, 'w') as f:
                json.dump(self.tasks, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving schedule: {e}")

    def add_task(self, name: str, cron_expr: str, task_type: str, params: Dict[str, Any]) -> bool:
        """Add a new scheduled task."""
        if not croniter.is_valid(cron_expr):
            logger.error(f"Invalid cron expression: {cron_expr}")
            return False

        task = {
            "name": name,
            "cron": cron_expr,
            "type": task_type,
            "params": params,
            "last_run": None
        }

        # Check if name exists
        for t in self.tasks:
            if t["name"] == name:
                return False

        self.tasks.append(task)
        self._save_schedule()
        return True

    def remove_task(self, name: str) -> bool:
        """Remove a task by name."""
        initial_len = len(self.tasks)
        self.tasks = [t for t in self.tasks if t["name"] != name]
        if len(self.tasks) < initial_len:
            self._save_schedule()
            return True
        return False

    def list_tasks(self) -> List[Dict[str, Any]]:
        """List all tasks."""
        return self.tasks

    async def run_due_tasks(self) -> None:
        """Check and run pending tasks."""
        now = datetime.now()

        for task in self.tasks:
            try:
                cron = croniter(task["cron"], now)
                prev_run_time = cron.get_prev(datetime)

                last_run_str = task.get("last_run")
                if last_run_str:
                    last_run = datetime.fromisoformat(last_run_str)
                else:
                    last_run = datetime.min

                if prev_run_time > last_run:
                    logger.info(f"Running task: {task['name']}")
                    await self._execute_task(task)
                    task["last_run"] = now.isoformat()
                    self._save_schedule()
            except Exception as e:
                logger.error(f"Error checking task {task.get('name')}: {e}")

    async def _execute_task(self, task: Dict[str, Any]) -> None:
        """Execute a single task."""
        task_type = task["type"]
        params = task["params"]

        try:
            if task_type == "organize_by_type":
                await self.organizer.organize_by_type(
                    Path(params["source"]),
                    Path(params["target"]),
                    move=True
                )
            elif task_type == "organize_by_date":
                await self.organizer.organize_by_date(
                    Path(params["source"]),
                    Path(params["target"]),
                    move=True
                )
            elif task_type == "cleanup":
                await self.organizer.cleanup_old_files(
                    Path(params["dir"]),
                    params["days"],
                    recursive=params.get("recursive", False)
                )
            # Add other types as needed

        except Exception as e:
            logger.error(f"Task execution failed: {e}")

    async def run_daemon(self) -> None:
        """Run scheduler loop."""
        logger.info("Scheduler daemon started.")
        while True:
            await self.run_due_tasks()
            await asyncio.sleep(60)

if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="TFM Scheduler Daemon")
    parser.add_argument("--daemon", action="store_true", help="Run in daemon mode")
    args = parser.parse_args()

    if args.daemon:
        try:
            scheduler = TaskScheduler()
            asyncio.run(scheduler.run_daemon())
        except KeyboardInterrupt:
            pass
