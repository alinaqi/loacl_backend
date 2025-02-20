"""
Task repository module.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from app.core.logger import get_logger
from app.models.tasks import Task, TaskCreate, TaskStatus, TaskUpdate
from app.repositories.base import BaseRepository

logger = get_logger(__name__)


class TaskRepository(BaseRepository[Task, TaskCreate, TaskUpdate]):
    """Repository for task operations."""

    def __init__(self):
        """Initialize the repository."""
        super().__init__("tasks", Task)

    async def get_pending_tasks(self, limit: int = 100) -> List[Task]:
        """
        Get pending tasks that are ready to be executed.

        Args:
            limit: Maximum number of tasks to return

        Returns:
            List[Task]: List of pending tasks
        """
        try:
            response = (
                await self.client.table(self.table_name)
                .select("*")
                .eq("status", TaskStatus.PENDING)
                .lte("scheduled_for", datetime.utcnow().isoformat())
                .order("priority", desc=True)
                .limit(limit)
                .execute()
            )

            return [Task(**task) for task in response.data]
        except Exception as e:
            logger.error("Failed to get pending tasks", error=str(e))
            raise

    async def get_running_tasks(self) -> List[Task]:
        """
        Get currently running tasks.

        Returns:
            List[Task]: List of running tasks
        """
        try:
            response = (
                await self.client.table(self.table_name)
                .select("*")
                .eq("status", TaskStatus.RUNNING)
                .execute()
            )

            return [Task(**task) for task in response.data]
        except Exception as e:
            logger.error("Failed to get running tasks", error=str(e))
            raise

    async def mark_task_started(self, task_id: UUID) -> None:
        """
        Mark a task as started.

        Args:
            task_id: Task ID
        """
        try:
            update_data = TaskUpdate(
                status=TaskStatus.RUNNING,
                started_at=datetime.utcnow(),
            )
            await self.update(task_id, update_data)
        except Exception as e:
            logger.error("Failed to mark task as started", error=str(e))
            raise

    async def mark_task_completed(
        self, task_id: UUID, result: Optional[dict] = None
    ) -> None:
        """
        Mark a task as completed.

        Args:
            task_id: Task ID
            result: Optional task result
        """
        try:
            update_data = TaskUpdate(
                status=TaskStatus.COMPLETED,
                completed_at=datetime.utcnow(),
                result=result,
            )
            await self.update(task_id, update_data)
        except Exception as e:
            logger.error("Failed to mark task as completed", error=str(e))
            raise

    async def mark_task_failed(
        self, task_id: UUID, error: str, should_retry: bool = True
    ) -> None:
        """
        Mark a task as failed.

        Args:
            task_id: Task ID
            error: Error message
            should_retry: Whether to retry the task
        """
        try:
            task = await self.get(task_id)
            if not task:
                return

            # Check if we should retry
            max_retries = task.max_retries or 0
            current_retries = task.retry_count or 0
            can_retry = should_retry and current_retries < max_retries

            update_data = TaskUpdate(
                status=TaskStatus.PENDING if can_retry else TaskStatus.FAILED,
                error=error,
                retry_count=current_retries + 1 if can_retry else current_retries,
                completed_at=None if can_retry else datetime.utcnow(),
            )
            await self.update(task_id, update_data)
        except Exception as e:
            logger.error("Failed to mark task as failed", error=str(e))
            raise

    async def cancel_task(self, task_id: UUID) -> None:
        """
        Cancel a task.

        Args:
            task_id: Task ID
        """
        try:
            update_data = TaskUpdate(
                status=TaskStatus.CANCELLED,
                completed_at=datetime.utcnow(),
            )
            await self.update(task_id, update_data)
        except Exception as e:
            logger.error("Failed to cancel task", error=str(e))
            raise
