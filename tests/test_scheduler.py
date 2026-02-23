"""
Tests for the scheduler system.
"""

import pytest
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from src.file_manager.scheduler import TaskScheduler

@pytest.fixture
def temp_schedule_file(tmp_path):
    return tmp_path / "schedule.json"

def test_add_remove_task(temp_schedule_file):
    scheduler = TaskScheduler(temp_schedule_file)

    # Add
    assert scheduler.add_task("test_task", "* * * * *", "/tmp/test", "cleanup")
    tasks = scheduler.list_tasks()
    assert len(tasks) == 1
    assert tasks[0]["name"] == "test_task"

    # Remove
    assert scheduler.remove_task("test_task")
    tasks = scheduler.list_tasks()
    assert len(tasks) == 0

def test_add_invalid_cron(temp_schedule_file):
    scheduler = TaskScheduler(temp_schedule_file)
    assert not scheduler.add_task("bad_cron", "invalid", "/tmp", "cleanup")
    assert len(scheduler.list_tasks()) == 0

def test_run_pending_tasks(temp_schedule_file):
    scheduler = TaskScheduler(temp_schedule_file)
    target_dir = Path("/tmp/test_scheduler_run")
    target_dir.mkdir(parents=True, exist_ok=True)

    # Create a task that runs every minute
    # To force it to run, we can set last_run to 2 minutes ago
    cron = "* * * * *"
    scheduler.add_task("run_me", cron, str(target_dir), "find_duplicates")

    # Manually set last_run to ensure it triggers
    tasks = scheduler.list_tasks()
    tasks[0]["last_run"] = (datetime.now() - timedelta(minutes=2)).isoformat()
    scheduler._save_tasks(tasks)

    # Mock organizer to verify execution?
    # Or just check if last_run updated.

    initial_last_run = tasks[0]["last_run"]

    # We need to mock FileOrganizer in scheduler to avoid actual operations or errors
    # But for find_duplicates it just logs.

    scheduler.run_pending_tasks()

    tasks = scheduler.list_tasks()
    new_last_run = tasks[0]["last_run"]

    assert new_last_run != initial_last_run
    assert datetime.fromisoformat(new_last_run) > datetime.fromisoformat(initial_last_run)
