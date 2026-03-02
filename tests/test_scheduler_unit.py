import pytest
from unittest.mock import AsyncMock
from datetime import datetime, timedelta
from src.file_manager.scheduler import TaskScheduler

@pytest.fixture
def scheduler(tmp_path):
    schedule_file = tmp_path / "test_schedule.json"
    return TaskScheduler(schedule_file)

def test_add_job(scheduler):
    params = {"source": ".", "target": "dest"}
    scheduler.add_job("test_job", "* * * * *", "organize_by_type", params)

    assert len(scheduler.jobs) == 1
    assert scheduler.jobs[0]["name"] == "test_job"
    assert scheduler.jobs[0]["cron"] == "* * * * *"

def test_add_invalid_cron(scheduler):
    scheduler.add_job("bad_cron", "invalid", "cleanup", {})
    # Should not add
    assert len(scheduler.jobs) == 0

def test_remove_job(scheduler):
    scheduler.add_job("job1", "* * * * *", "cleanup", {})
    assert scheduler.remove_job("job1")
    assert len(scheduler.jobs) == 0
    assert not scheduler.remove_job("job1")

@pytest.mark.asyncio
async def test_run_pending(scheduler):
    # Mock organizer methods
    # Use AsyncMock for async methods
    scheduler.organizer.organize_by_type = AsyncMock(return_value={})

    # Add a job
    params = {"source": ".", "target": "dest"}
    scheduler.add_job("run_me", "* * * * *", "organize_by_type", params)

    # Force run by setting last_run to 70 seconds ago
    job = scheduler.jobs[0]
    job["last_run"] = (datetime.now() - timedelta(seconds=70)).timestamp()

    await scheduler.run_pending()

    # Check if executed
    assert scheduler.organizer.organize_by_type.called

    # Check if last_run updated
    assert job["last_run"] > (datetime.now() - timedelta(seconds=5)).timestamp()
