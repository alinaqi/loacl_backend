"""
Task service module.
"""

import asyncio
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Type
from uuid import UUID, uuid4

from fastapi import BackgroundTasks

from app.core.logger import get_logger
from app.models.tasks import Task, TaskCreate, TaskPriority, TaskStatus
from app.repositories.task import TaskRepository
from app.services.base import BaseService

logger = get_logger(__name__)


class TaskService(BaseService):
    """Service for managing background tasks."""

    def __init__(self, task_repository: TaskRepository):
        """
        Initialize the service.

        Args:
            task_repository: Repository for task operations
        """
        super().__init__()
        self.task_repository = task_repository
        self._task_handlers: Dict[str, Callable] = {}
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None

    def register_handler(self, task_type: str, handler: Callable) -> None:
        """
        Register a handler for a task type.

        Args:
            task_type: Type of task
            handler: Handler function
        """
        self._task_handlers[task_type] = handler

    async def create_task(
        self,
        name: str,
        task_type: str,
        payload: Dict[str, Any],
        priority: TaskPriority = TaskPriority.NORMAL,
        scheduled_for: Optional[datetime] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Task:
        """
        Create a new task.

        Args:
            name: Task name
            task_type: Type of task
            payload: Task payload
            priority: Task priority
            scheduled_for: When to execute the task
            timeout: Task timeout in seconds
            max_retries: Maximum number of retries
            metadata: Additional metadata

        Returns:
            Task: Created task
        """
        task_data = TaskCreate(
            name=name,
            task_type=task_type,
            payload=payload,
            priority=priority,
            scheduled_for=scheduled_for,
            timeout=timeout,
            retry_count=0,
            metadata=metadata or {},
        )

        response = await self.task_repository.create(task_data)
        return Task(**response.data[0])

    async def schedule_task(
        self,
        background_tasks: BackgroundTasks,
        name: str,
        task_type: str,
        payload: Dict[str, Any],
        priority: TaskPriority = TaskPriority.NORMAL,
        scheduled_for: Optional[datetime] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Task:
        """
        Schedule a task for execution.

        Args:
            background_tasks: FastAPI background tasks
            name: Task name
            task_type: Type of task
            payload: Task payload
            priority: Task priority
            scheduled_for: When to execute the task
            timeout: Task timeout in seconds
            max_retries: Maximum number of retries
            metadata: Additional metadata

        Returns:
            Task: Created task
        """
        task = await self.create_task(
            name=name,
            task_type=task_type,
            payload=payload,
            priority=priority,
            scheduled_for=scheduled_for,
            timeout=timeout,
            max_retries=max_retries,
            metadata=metadata,
        )

        # If task is scheduled for immediate execution, run it in background
        if not scheduled_for or scheduled_for <= datetime.utcnow():
            background_tasks.add_task(self._execute_task, task.id)

        return task

    async def start_worker(self) -> None:
        """Start the background task worker."""
        if self._running:
            return

        self._running = True
        self._worker_task = asyncio.create_task(self._worker_loop())
        logger.info("Background task worker started")

    async def stop_worker(self) -> None:
        """Stop the background task worker."""
        if not self._running:
            return

        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        logger.info("Background task worker stopped")

    async def _worker_loop(self) -> None:
        """Background task worker loop."""
        while self._running:
            try:
                # Get pending tasks
                tasks = await self.task_repository.get_pending_tasks(limit=10)

                # Process each task
                for task in tasks:
                    asyncio.create_task(self._execute_task(task.id))

                # Sleep before next iteration
                await asyncio.sleep(1)
            except Exception as e:
                logger.error("Error in worker loop", error=str(e))
                await asyncio.sleep(5)  # Sleep longer on error

    async def _execute_task(self, task_id: UUID) -> None:
        """
        Execute a task.

        Args:
            task_id: Task ID
        """
        try:
            # Get task
            task = await self.task_repository.get(task_id)
            if not task or task.status not in [TaskStatus.PENDING]:
                return

            # Get handler
            handler = self._task_handlers.get(task.task_type)
            if not handler:
                await self.task_repository.mark_task_failed(
                    task_id,
                    f"No handler registered for task type: {task.task_type}",
                    should_retry=False,
                )
                return

            # Mark task as started
            await self.task_repository.mark_task_started(task_id)

            # Execute handler with timeout if specified
            try:
                if task.timeout:
                    async with asyncio.timeout(task.timeout):
                        result = await handler(task.payload)
                else:
                    result = await handler(task.payload)

                # Mark task as completed
                await self.task_repository.mark_task_completed(task_id, result)

            except asyncio.TimeoutError:
                await self.task_repository.mark_task_failed(
                    task_id,
                    f"Task timed out after {task.timeout} seconds",
                )
            except Exception as e:
                await self.task_repository.mark_task_failed(task_id, str(e))

        except Exception as e:
            logger.error(f"Error executing task {task_id}", error=str(e))
            try:
                await self.task_repository.mark_task_failed(
                    task_id,
                    f"Internal error: {str(e)}",
                    should_retry=False,
                )
            except Exception:
                pass  # Ignore errors in error handling
