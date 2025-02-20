"""
Tests for the task system.
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import BackgroundTasks

from app.models.tasks import Task, TaskCreate, TaskPriority, TaskStatus
from app.repositories.task import TaskRepository
from app.services.tasks import TaskService


@pytest.fixture
def task_repository():
    """Create a mock task repository."""
    return AsyncMock(spec=TaskRepository)


@pytest.fixture
def task_service(task_repository):
    """Create a task service instance."""
    return TaskService(task_repository=task_repository)


@pytest.fixture
def sample_task():
    """Create a sample task."""
    return Task(
        id=uuid4(),
        name="test_task",
        task_type="test",
        status=TaskStatus.PENDING,
        priority=TaskPriority.NORMAL,
        payload={"key": "value"},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


async def test_create_task(task_service, task_repository, sample_task):
    """Test creating a task."""
    # Setup
    task_repository.create.return_value.data = [sample_task.model_dump()]

    # Execute
    task = await task_service.create_task(
        name="test_task",
        task_type="test",
        payload={"key": "value"},
    )

    # Verify
    assert task.name == "test_task"
    assert task.task_type == "test"
    assert task.payload == {"key": "value"}
    task_repository.create.assert_called_once()


async def test_schedule_immediate_task(task_service, task_repository, sample_task):
    """Test scheduling an immediate task."""
    # Setup
    task_repository.create.return_value.data = [sample_task.model_dump()]
    background_tasks = BackgroundTasks()

    # Execute
    task = await task_service.schedule_task(
        background_tasks=background_tasks,
        name="test_task",
        task_type="test",
        payload={"key": "value"},
    )

    # Verify
    assert task.name == "test_task"
    assert len(background_tasks.tasks) == 1


async def test_schedule_future_task(task_service, task_repository, sample_task):
    """Test scheduling a future task."""
    # Setup
    task_repository.create.return_value.data = [sample_task.model_dump()]
    background_tasks = BackgroundTasks()
    scheduled_time = datetime.utcnow() + timedelta(hours=1)

    # Execute
    task = await task_service.schedule_task(
        background_tasks=background_tasks,
        name="test_task",
        task_type="test",
        payload={"key": "value"},
        scheduled_for=scheduled_time,
    )

    # Verify
    assert task.name == "test_task"
    assert len(background_tasks.tasks) == 0  # No immediate execution


async def test_execute_task_success(task_service, task_repository, sample_task):
    """Test successful task execution."""
    # Setup
    task_repository.get.return_value = sample_task
    handler_result = {"status": "success"}

    async def mock_handler(payload):
        return handler_result

    task_service.register_handler("test", mock_handler)

    # Execute
    await task_service._execute_task(sample_task.id)

    # Verify
    task_repository.mark_task_started.assert_called_once_with(sample_task.id)
    task_repository.mark_task_completed.assert_called_once_with(
        sample_task.id, handler_result
    )


async def test_execute_task_failure(task_service, task_repository, sample_task):
    """Test failed task execution."""
    # Setup
    task_repository.get.return_value = sample_task
    error_message = "Test error"

    async def mock_handler(payload):
        raise ValueError(error_message)

    task_service.register_handler("test", mock_handler)

    # Execute
    await task_service._execute_task(sample_task.id)

    # Verify
    task_repository.mark_task_started.assert_called_once_with(sample_task.id)
    task_repository.mark_task_failed.assert_called_once_with(
        sample_task.id, error_message
    )


async def test_execute_task_timeout(task_service, task_repository):
    """Test task timeout."""
    # Setup
    task = Task(
        id=uuid4(),
        name="test_task",
        task_type="test",
        status=TaskStatus.PENDING,
        priority=TaskPriority.NORMAL,
        payload={"key": "value"},
        timeout=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    task_repository.get.return_value = task

    async def mock_handler(payload):
        await asyncio.sleep(2)
        return {"status": "success"}

    task_service.register_handler("test", mock_handler)

    # Execute
    await task_service._execute_task(task.id)

    # Verify
    task_repository.mark_task_started.assert_called_once_with(task.id)
    task_repository.mark_task_failed.assert_called_once()
    assert "timed out" in task_repository.mark_task_failed.call_args[0][1]


async def test_worker_loop(task_service, task_repository, sample_task):
    """Test worker loop."""
    # Setup
    task_repository.get_pending_tasks.return_value = [sample_task]
    handler_result = {"status": "success"}

    async def mock_handler(payload):
        return handler_result

    task_service.register_handler("test", mock_handler)

    # Start worker
    await task_service.start_worker()
    await asyncio.sleep(0.1)  # Let worker process task
    await task_service.stop_worker()

    # Verify
    task_repository.get_pending_tasks.assert_called()
    task_repository.mark_task_started.assert_called_with(sample_task.id)
    task_repository.mark_task_completed.assert_called_with(
        sample_task.id, handler_result
    )
