import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from src.file_manager.scheduler import TaskScheduler
from datetime import datetime, timedelta

@pytest.fixture
def scheduler(tmp_path):
    schedule_file = tmp_path / "schedule.json"
    return TaskScheduler(schedule_file)

def test_add_remove_job(scheduler):
    assert scheduler.add_job("job1", "* * * * *", "cleanup", {"dir": "/tmp", "days": 30})
    jobs = scheduler.list_jobs()
    assert len(jobs) == 1
    assert jobs[0]["name"] == "job1"

    assert scheduler.remove_job("job1")
    assert len(scheduler.list_jobs()) == 0

def test_invalid_cron(scheduler):
    assert not scheduler.add_job("job_bad", "invalid cron", "cleanup", {})

@pytest.mark.asyncio
async def test_run_pending(scheduler):
    # Mock organizer
    scheduler.organizer.cleanup_old_files = AsyncMock()

    # Add a job that should run (e.g., cron is every minute, last run never)
    scheduler.add_job("test_job", "* * * * *", "cleanup", {"dir": "/tmp", "days": 30})

    # Run pending
    await scheduler.run_pending()

    # Should have run
    scheduler.organizer.cleanup_old_files.assert_called_once()

    # Check last_run update
    updated_jobs = scheduler.list_jobs()
    assert updated_jobs[0]["last_run"] is not None

    # Run again immediately - should NOT run
    scheduler.organizer.cleanup_old_files.reset_mock()
    await scheduler.run_pending()
    scheduler.organizer.cleanup_old_files.assert_not_called()

@pytest.mark.asyncio
async def test_run_now(scheduler):
    scheduler.organizer.cleanup_old_files = AsyncMock()

    scheduler.add_job("manual_job", "0 0 1 1 *", "cleanup", {"dir": "/tmp", "days": 30})

    assert await scheduler.run_now("manual_job")
    scheduler.organizer.cleanup_old_files.assert_called_once()

    assert not await scheduler.run_now("non_existent_job")
