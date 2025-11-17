"""Task lifecycle business logic."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Sequence

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models import Device, Task, TaskLog, TaskStatus, User


class TaskService:
    """Service encapsulating task queue operations."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def enqueue_task(
        self,
        *,
        user: User,
        device: Device,
        task_type: str,
        payload: dict[str, Any],
        priority: int = 0,
    ) -> Task:
        """Create a new task for a given device."""

        task = Task(
            user_id=user.id,
            user_key=user.user_key,
            device_id=device.id,
            device_identifier=device.device_id,
            type=task_type,
            payload=payload,
            priority=priority,
            status=TaskStatus.PENDING,
        )
        self._session.add(task)
        self._session.flush()
        return task

    def get_by_uuid(self, task_uuid: str) -> Task | None:
        """Fetch a task by its external UUID."""

        stmt = select(Task).where(Task.task_uuid == task_uuid)
        return self._session.scalar(stmt)

    def fetch_next_pending_task(
        self, *, user_key: str, device_identifier: str
    ) -> Task | None:
        """Retrieve the next pending task for the device."""

        stmt: Select[Task] = (
            select(Task)
            .where(Task.user_key == user_key)
            .where(Task.device_identifier == device_identifier)
            .where(Task.status == TaskStatus.PENDING)
            .order_by(Task.priority.desc(), Task.created_at.asc())
            .limit(1)
        )
        task = self._session.scalar(stmt)
        if not task:
            return None

        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now(timezone.utc)
        self._session.flush()
        return task

    def fetch_pending_batch(
        self, *, user_key: str, device_identifier: str, limit: int = 1
    ) -> Sequence[Task]:
        """Retrieve a batch of pending tasks without status transition."""

        stmt: Select[Task] = (
            select(Task)
            .where(Task.user_key == user_key)
            .where(Task.device_identifier == device_identifier)
            .where(Task.status == TaskStatus.PENDING)
            .order_by(Task.priority.desc(), Task.created_at.asc())
            .limit(limit)
        )
        return list(self._session.scalars(stmt))

    def mark_running(self, task: Task) -> Task:
        """Ensure a task is marked as running."""

        task.status = TaskStatus.RUNNING
        task.started_at = task.started_at or datetime.now(timezone.utc)
        self._session.flush()
        return task

    def update_status(
        self,
        task: Task,
        *,
        status: TaskStatus,
        log: str | None = None,
        result: dict[str, Any] | None = None,
        stats: dict[str, Any] | None = None,
        error_message: str | None = None,
    ) -> Task:
        """Update task status after execution."""

        task.status = status
        task.finished_at = datetime.now(timezone.utc)
        if log:
            task.log = log
        if error_message:
            task.error_message = error_message
        if result:
            self.append_log(task, level="DEBUG", message=f"result: {result!r}")
        if stats:
            self.append_log(task, level="DEBUG", message=f"stats: {stats!r}")
        self._session.flush()
        return task

    def append_log(self, task: Task, *, level: str = "INFO", message: str) -> TaskLog:
        """Append a structured log entry to the task."""

        entry = TaskLog(task_id=task.id, level=level, message=message)
        self._session.add(entry)
        self._session.flush()
        return entry

    def list_recent_tasks(
        self, *, device: Device, limit: int = 20
    ) -> Sequence[Task]:
        """List recent tasks assigned to a device."""

        stmt = (
            select(Task)
            .where(Task.device_id == device.id)
            .order_by(Task.created_at.desc())
            .limit(limit)
        )
        return list(self._session.scalars(stmt))

