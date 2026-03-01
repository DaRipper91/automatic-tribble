"""
Task Scheduler for File Manager Automation.
"""

import json
import logging
import asyncio
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from croniter import croniter

from .automation import FileOrganizer

logger = logging.getLogger(__name__)

class TaskScheduler:
    """Manages scheduled automation tasks."""

    def __init__(self, schedule_file: Optional[Path] = None):
        if schedule_file is None:
            home = Path.home()
            tfm_dir = home / ".tfm"
            tfm_dir.mkdir(exist_ok=True)
            self.schedule_file = tfm_dir / "schedule.json"
        else:
            self.schedule_file = schedule_file

        self.organizer = FileOrganizer()
        self.jobs: List[Dict[str, Any]] = []
        self._load_jobs()

    def _load_jobs(self):
        """Load jobs from JSON file."""
        if self.schedule_file.exists():
            try:
                with open(self.schedule_file, "r") as f:
                    self.jobs = json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                logger.error(f"Failed to load schedule: {e}")
                self.jobs = []
        else:
            self.jobs = []

    def _save_jobs(self):
        """Save jobs to JSON file."""
        try:
            with open(self.schedule_file, "w") as f:
                json.dump(self.jobs, f, indent=2)
        except OSError as e:
            logger.error(f"Failed to save schedule: {e}")

    def add_job(self, name: str, cron_expr: str, task_type: str, params: Dict[str, Any]) -> bool:
        """Add a new scheduled job."""
        if not croniter.is_valid(cron_expr):
            logger.error(f"Invalid cron expression: {cron_expr}")
            return False

        # Validate task type
        valid_types = ["organize_by_type", "organize_by_date", "cleanup", "duplicates"]
        if task_type not in valid_types:
            logger.error(f"Invalid task type: {task_type}")
            return False

        job = {
            "name": name,
            "cron": cron_expr,
            "type": task_type,
            "params": params,
            "last_run": None,
            "enabled": True
        }

        # Remove existing job with same name if exists
        self.jobs = [j for j in self.jobs if j["name"] != name]
        self.jobs.append(job)
        self._save_jobs()
        return True

    def remove_job(self, name: str) -> bool:
        """Remove a job by name."""
        initial_len = len(self.jobs)
        self.jobs = [j for j in self.jobs if j["name"] != name]
        if len(self.jobs) < initial_len:
            self._save_jobs()
            return True
        return False

    def list_jobs(self) -> List[Dict[str, Any]]:
        """List all jobs."""
        return self.jobs

    async def run_pending(self):
        """Check and run pending jobs."""
        now = datetime.now()
        for job in self.jobs:
            if not job.get("enabled", True):
                continue

            try:
                cron = croniter(job["cron"], now)

                last_run_ts = job.get("last_run")
                prev_run_time = cron.get_prev(datetime)

                should_run = False
                if last_run_ts is None:
                    # If never run, run if scheduled time was within last 60s
                    if (now - prev_run_time).total_seconds() < 60:
                        should_run = True
                else:
                    last_run_dt = datetime.fromtimestamp(last_run_ts)
                    if prev_run_time > last_run_dt:
                        should_run = True

                if should_run:
                    logger.info(f"Running job: {job['name']}")
                    await self._execute_job(job)
                    job["last_run"] = now.timestamp()
                    self._save_jobs()
            except Exception as e:
                logger.error(f"Error checking job {job['name']}: {e}")

    async def run_now(self, job_name: str) -> bool:
        """Manually run a specific job immediately."""
        job = next((j for j in self.jobs if j["name"] == job_name), None)
        if not job:
            return False

        logger.info(f"Manually running job: {job_name}")
        await self._execute_job(job)
        job["last_run"] = time.time()
        self._save_jobs()
        return True

    async def _execute_job(self, job: Dict[str, Any]):
        """Execute a single job."""
        task_type = job["type"]
        params = job["params"]

        try:
            if task_type == "organize_by_type":
                await self.organizer.organize_by_type(
                    Path(params["source"]), Path(params["target"]), move=params.get("move", True)
                )
            elif task_type == "organize_by_date":
                await self.organizer.organize_by_date(
                    Path(params["source"]), Path(params["target"]), move=params.get("move", True)
                )
            elif task_type == "cleanup":
                await self.organizer.cleanup_old_files(
                    Path(params["dir"]), params["days"], params.get("recursive", False)
                )
            elif task_type == "duplicates":
                 dups = await self.organizer.find_duplicates(
                     Path(params["dir"]), params.get("recursive", False)
                 )
                 logger.info(f"Scheduled duplicate scan found {len(dups)} groups.")

        except Exception as e:
            logger.error(f"Job {job['name']} failed: {e}")

    async def run_daemon(self):
        """Run the scheduler loop."""
        logger.info("Scheduler daemon started.")
        print("Scheduler daemon started. Press Ctrl+C to stop.")
        while True:
            await self.run_pending()
            await asyncio.sleep(60)

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        filename=Path.home() / ".tfm" / "scheduler.log",
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    scheduler = TaskScheduler()
    try:
        asyncio.run(scheduler.run_daemon())
    except KeyboardInterrupt:
        print("Scheduler stopped.")
