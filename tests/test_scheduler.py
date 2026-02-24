import pytest
import json
from pathlib import Path
from src.file_manager.scheduler import TaskScheduler

@pytest.fixture
def scheduler(tmp_path):
    schedule_file = tmp_path / "schedule.json"
    return TaskScheduler(schedule_file)

def test_add_remove_task(scheduler):
    assert scheduler.add_task("test", "* * * * *", "cleanup", {"dir": "/tmp", "days": 1})
    assert len(scheduler.list_tasks()) == 1
    assert scheduler.tasks[0]["name"] == "test"

    assert scheduler.remove_task("test")
    assert len(scheduler.list_tasks()) == 0

def test_invalid_cron(scheduler):
    assert not scheduler.add_task("bad", "invalid", "cleanup", {})
